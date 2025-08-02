#!/usr/bin/env python3
"""
Student Management 테스트 파일

이 파일은 Student Management 시스템의 기본 기능을 테스트합니다.
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestStudentDatabase(unittest.TestCase):
    """Student Database 테스트 클래스"""
    
    def setUp(self):
        """테스트 전 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # 데이터베이스 연결
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 외래키 제약조건 활성화
        self.cursor.execute('PRAGMA foreign_keys = ON')
        
        # 테이블 생성
        self.create_tables()
    
    def tearDown(self):
        """테스트 후 정리"""
        self.conn.close()
        os.unlink(self.db_path)
    
    def create_tables(self):
        """테스트용 테이블 생성"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number TEXT UNIQUE,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT NOT NULL,
                score REAL,
                evaluation_date DATE,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()
    
    def test_add_student(self):
        """학생 추가 테스트"""
        # 학생 추가
        student_number = "2024001"
        name = "홍길동"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute(
            'INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
            (student_number, name, now, now)
        )
        self.conn.commit()
        
        # 추가된 학생 확인
        self.cursor.execute('SELECT student_number, name FROM students WHERE student_number = ?', (student_number,))
        result = self.cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], student_number)
        self.assertEqual(result[1], name)
    
    def test_add_evaluation(self):
        """평가 추가 테스트"""
        # 먼저 학생 추가
        student_number = "2024002"
        name = "김철수"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute(
            'INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
            (student_number, name, now, now)
        )
        self.conn.commit()
        
        # 학생 ID 가져오기
        self.cursor.execute('SELECT id FROM students WHERE student_number = ?', (student_number,))
        student_id = self.cursor.fetchone()[0]
        
        # 평가 추가
        subject = "수학"
        score = 85.5
        eval_date = "2024-01-20"
        notes = "중간고사"
        
        self.cursor.execute(
            'INSERT INTO evaluations (student_id, subject, score, evaluation_date, notes) VALUES (?, ?, ?, ?, ?)',
            (student_id, subject, score, eval_date, notes)
        )
        self.conn.commit()
        
        # 추가된 평가 확인
        self.cursor.execute('SELECT subject, score, evaluation_date, notes FROM evaluations WHERE student_id = ?', (student_id,))
        result = self.cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], subject)
        self.assertEqual(result[1], score)
        self.assertEqual(result[2], eval_date)
        self.assertEqual(result[3], notes)
    
    def test_duplicate_student_number(self):
        """중복 학번 테스트"""
        student_number = "2024003"
        name1 = "이영희"
        name2 = "박민수"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 첫 번째 학생 추가
        self.cursor.execute(
            'INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
            (student_number, name1, now, now)
        )
        self.conn.commit()
        
        # 동일한 학번으로 두 번째 학생 추가 시도 (실패해야 함)
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute(
                'INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
                (student_number, name2, now, now)
            )
            self.conn.commit()
    
    def test_delete_student_with_evaluations(self):
        """평가가 있는 학생 삭제 테스트"""
        # 학생 추가
        student_number = "2024004"
        name = "정수진"
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute(
            'INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
            (student_number, name, now, now)
        )
        self.conn.commit()
        
        # 학생 ID 가져오기
        self.cursor.execute('SELECT id FROM students WHERE student_number = ?', (student_number,))
        student_id = self.cursor.fetchone()[0]
        
        # 평가 추가
        self.cursor.execute(
            'INSERT INTO evaluations (student_id, subject, score, evaluation_date, notes) VALUES (?, ?, ?, ?, ?)',
            (student_id, "영어", 90.0, "2024-01-20", "기말고사")
        )
        self.conn.commit()
        
        # 학생 삭제
        self.cursor.execute('DELETE FROM students WHERE student_number = ?', (student_number,))
        self.conn.commit()
        
        # 학생이 삭제되었는지 확인
        self.cursor.execute('SELECT COUNT(*) FROM students WHERE student_number = ?', (student_number,))
        student_count = self.cursor.fetchone()[0]
        self.assertEqual(student_count, 0)
        
        # 평가도 함께 삭제되었는지 확인
        self.cursor.execute('SELECT COUNT(*) FROM evaluations WHERE student_id = ?', (student_id,))
        eval_count = self.cursor.fetchone()[0]
        self.assertEqual(eval_count, 0)
    
    def test_date_validation(self):
        """날짜 검증 테스트"""
        def is_valid_date(date_str):
            if not date_str:
                return False
            import re
            pattern = r'^\d{4}-\d{2}-\d{2}$'
            if not re.match(pattern, date_str):
                return False
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        
        # 유효한 날짜
        self.assertTrue(is_valid_date("2024-01-20"))
        self.assertTrue(is_valid_date("2024-12-31"))
        
        # 무효한 날짜
        self.assertFalse(is_valid_date("2024-13-01"))  # 잘못된 월
        self.assertFalse(is_valid_date("2024-01-32"))  # 잘못된 일
        self.assertFalse(is_valid_date("2024/01/20"))  # 잘못된 형식
        self.assertFalse(is_valid_date(""))  # 빈 문자열
        self.assertFalse(is_valid_date(None))  # None

def run_tests():
    """테스트 실행"""
    print("🧪 Student Management 테스트를 시작합니다...")
    
    # 테스트 스위트 생성
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestStudentDatabase)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 출력
    if result.wasSuccessful():
        print("\n✅ 모든 테스트가 성공적으로 통과했습니다!")
    else:
        print(f"\n❌ {len(result.failures)}개의 테스트가 실패했습니다.")
        for test, traceback in result.failures:
            print(f"\n실패한 테스트: {test}")
            print(f"오류: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests() 