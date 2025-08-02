import sys
import sqlite3
from datetime import datetime
import csv
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView, QMessageBox,
    QMenuBar, QMenu, QAction, QFileDialog
)

# 상수 정의
DB_FILE = 'student.db'
STUDENT_CSV_HEADER = ["학번", "이름", "등록일", "최근평가일"]
EVAL_CSV_HEADER = ["학번", "이름", "과목", "점수", "평가일", "비고"]

# 날짜 검증 함수
def is_valid_date(date_str):
    if not date_str:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

class StudentDatabase(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("학생 관리 시스템 (PyQt5)")
        # 해상도의 80% 크기로, 화면 중앙에 위치
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        win_width = int(screen_width * 0.8)
        win_height = int(screen_height * 0.8)
        self.resize(win_width, win_height)
        # 중앙 정렬
        x = screen_geometry.x() + (screen_width - win_width) // 2
        y = screen_geometry.y() + (screen_height - win_height) // 2
        self.move(x, y)

        # 폰트 크기 비율로 동적 조정 (기본 14, FHD 기준 1080px에서 14)
        base_height = 1080
        base_font_size = 14
        # 폰트 크기 비율을 0.8배로 줄임
        font_size = max(10, int(base_font_size * (win_height / base_height) * 0.8))
        from PyQt5.QtGui import QFont
        app_font = QFont()
        app_font.setPointSize(font_size)
        QApplication.setFont(app_font)
        self.conn = sqlite3.connect('student.db')
        self.cursor = self.conn.cursor()
        self.init_database()
        # 폰트 크기 비율로 동적 조정 (기본 14, FHD 기준 1080px에서 14)
        base_height = 1080
        base_font_size = 14
        font_size = max(10, int(base_font_size * (win_height / base_height) * 0.8))
        self.init_ui(font_size)
        self.load_students()

    def init_database(self):
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
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        self.conn.commit()

    def init_ui(self, font_size):
        main_layout = QVBoxLayout()

        # 메뉴바 추가 (폰트 크기 0.5배 적용)
        from PyQt5.QtGui import QFont
        self.menubar = QMenuBar(self)
        menubar_font = QFont()
        menubar_font.setPointSizeF(font_size * 0.6)
        self.menubar.setFont(menubar_font)
        file_menu = QMenu("파일", self)
        file_menu.setFont(menubar_font)
        export_csv_action = QAction("CSV 내보내기", self)
        export_csv_action.setFont(menubar_font)
        import_csv_action = QAction("CSV 불러오기", self)
        import_csv_action.setFont(menubar_font)
        export_csv_action.triggered.connect(self.export_csv)
        import_csv_action.triggered.connect(self.import_csv)
        file_menu.addAction(export_csv_action)
        file_menu.addAction(import_csv_action)
        self.menubar.addMenu(file_menu)
        main_layout.setMenuBar(self.menubar)

        # 학생 정보 입력
        input_group = QGroupBox("학생 정보")
        input_layout = QHBoxLayout()
        self.num_edit = QLineEdit()
        self.name_edit = QLineEdit()
        input_layout.addWidget(QLabel("학번:"))
        input_layout.addWidget(self.num_edit)
        input_layout.addWidget(QLabel("이름:"))
        input_layout.addWidget(self.name_edit)
        input_layout.addStretch(1)  # 입력창 좌측 정렬
        self.add_btn = QPushButton("추가")
        self.delete_btn = QPushButton("삭제")
        # 버튼 가로폭을 2배로 늘림
        # 평가 버튼 가로폭을 기준으로 학생 정보 버튼 가로폭도 동일하게 맞춤
        eval_btn_width = QPushButton("평가 추가").sizeHint().width() * 2
        for btn in [self.add_btn, self.delete_btn]:
            btn.setFixedWidth(eval_btn_width)
        input_layout.addWidget(self.add_btn)
        input_layout.addWidget(self.delete_btn)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # 학생 목록 테이블
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["학번", "이름", "등록일", "최근평가일"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        # 평가 정보 입력
        eval_group = QGroupBox("평가 정보")
        eval_layout = QHBoxLayout()
        self.subject_edit = QLineEdit()
        self.score_edit = QLineEdit()
        self.eval_date_edit = QLineEdit(datetime.now().strftime('%Y-%m-%d'))
        # 학번 입력창의 가로폭과 동일하게 조정
        num_width = self.num_edit.sizeHint().width()
        self.subject_edit.setFixedWidth(num_width)
        self.score_edit.setFixedWidth(num_width)
        self.eval_date_edit.setFixedWidth(num_width)
        from PyQt5.QtWidgets import QSizePolicy
        self.notes_edit = QLineEdit()
        # 비고 입력창이 평가 추가/삭제 버튼 바로 옆까지 확장되도록 설정
        self.notes_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        eval_layout.addWidget(QLabel("과목:"))
        eval_layout.addWidget(self.subject_edit)
        eval_layout.addWidget(QLabel("점수:"))
        eval_layout.addWidget(self.score_edit)
        eval_layout.addWidget(QLabel("평가일:"))
        eval_layout.addWidget(self.eval_date_edit)
        eval_layout.addWidget(QLabel("비고:"))
        eval_layout.addWidget(self.notes_edit)
        # addStretch 제거: 비고 입력창이 버튼 바로 옆까지 확장되도록
        self.eval_add_btn = QPushButton("평가 추가")
        self.eval_delete_btn = QPushButton("평가 삭제")
        # 평가 버튼 가로폭을 2배로 늘림
        eval_btn_width = self.eval_add_btn.sizeHint().width()
        for btn in [self.eval_add_btn, self.eval_delete_btn]:
            btn.setFixedWidth(eval_btn_width * 2)
        eval_layout.addWidget(self.eval_add_btn)
        eval_layout.addWidget(self.eval_delete_btn)
        eval_group.setLayout(eval_layout)
        main_layout.addWidget(eval_group)

        # 평가 목록 테이블
        self.eval_table = QTableWidget(0, 4)
        self.eval_table.setHorizontalHeaderLabels(["과목", "점수", "평가일", "비고"])
        self.eval_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.eval_table)

        self.setLayout(main_layout)

        # 이벤트 연결
        self.add_btn.clicked.connect(self.add_student)
        self.delete_btn.clicked.connect(self.delete_student)
        self.table.cellClicked.connect(self.on_student_select)
        self.eval_add_btn.clicked.connect(self.add_evaluation)
        self.eval_delete_btn.clicked.connect(self.delete_evaluation)

    def export_csv(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "학생정보 CSV 내보내기", "students.csv", "CSV Files (*.csv)", options=options)
        if file_path:
            try:
                self.cursor.execute('SELECT student_number, name, created_at, last_modified FROM students ORDER BY student_number')
                students = self.cursor.fetchall()
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(STUDENT_CSV_HEADER)
                    writer.writerows(students)
                eval_path = file_path.replace('.csv', '_evaluations.csv')
                self.cursor.execute('''SELECT s.student_number, s.name, e.subject, e.score, e.evaluation_date, e.notes FROM students s LEFT JOIN evaluations e ON s.id = e.student_id ORDER BY s.student_number, e.evaluation_date DESC''')
                evals = self.cursor.fetchall()
                with open(eval_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(EVAL_CSV_HEADER)
                    writer.writerows(evals)
                QMessageBox.information(self, "성공", f"학생정보와 평가정보가 CSV로 저장되었습니다.\n\n학생정보: {file_path}\n평가정보: {eval_path}")
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "오류", f"CSV 내보내기 중 오류 발생: {str(e)}")

    def import_csv(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "학생정보 CSV 불러오기", "", "CSV Files (*.csv)", options=options)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    students = list(reader)
                # 컬럼 검증
                if reader.fieldnames != STUDENT_CSV_HEADER:
                    QMessageBox.critical(self, "오류", f"학생정보 CSV의 컬럼이 올바르지 않습니다.\n필요: {STUDENT_CSV_HEADER}\n입력: {reader.fieldnames}")
                    return
                eval_path = file_path.replace('.csv', '_evaluations.csv')
                evals = []
                try:
                    with open(eval_path, 'r', encoding='utf-8-sig') as f:
                        eval_reader = csv.DictReader(f)
                        evals = list(eval_reader)
                    if eval_reader.fieldnames != EVAL_CSV_HEADER:
                        QMessageBox.critical(self, "오류", f"평가정보 CSV의 컬럼이 올바르지 않습니다.\n필요: {EVAL_CSV_HEADER}\n입력: {eval_reader.fieldnames}")
                        return
                except FileNotFoundError:
                    pass
                self.cursor.execute('DELETE FROM evaluations')
                self.cursor.execute('DELETE FROM students')
                for stu in students:
                    self.cursor.execute('INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
                        (stu["학번"], stu["이름"], stu["등록일"], stu["최근평가일"]))
                for ev in evals:
                    self.cursor.execute('SELECT id FROM students WHERE student_number=?', (ev["학번"],))
                    res = self.cursor.fetchone()
                    if res:
                        student_id = res[0]
                        # 점수 float 변환, 날짜 검증
                        score = None
                        try:
                            score = float(ev["점수"]) if ev["점수"] else None
                        except ValueError:
                            pass
                        eval_date = ev["평가일"] if is_valid_date(ev["평가일"]) else None
                        self.cursor.execute('INSERT INTO evaluations (student_id, subject, score, evaluation_date, notes) VALUES (?, ?, ?, ?, ?)',
                            (student_id, ev["과목"], score, eval_date, ev["비고"]))
                self.conn.commit()
                self.load_students()
                self.eval_table.setRowCount(0)
                QMessageBox.information(self, "성공", "CSV에서 학생정보와 평가정보를 불러왔습니다.")
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "오류", f"CSV 불러오기 중 오류 발생: {str(e)}")

    def load_students(self):
        self.table.setRowCount(0)
        self.cursor.execute('SELECT student_number, name, created_at, last_modified FROM students ORDER BY student_number')
        for row in self.cursor.fetchall():
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            for col, val in enumerate(row):
                self.table.setItem(row_pos, col, QTableWidgetItem(str(val)))

    def on_student_select(self, row, col):
        self.selected_student_number = self.table.item(row, 0).text()
        self.num_edit.setText(self.selected_student_number)
        self.name_edit.setText(self.table.item(row, 1).text())
        self.load_evaluations()

    def add_student(self):
        num = self.num_edit.text().strip()
        name = self.name_edit.text().strip()
        if not num or not name:
            QMessageBox.warning(self, "오류", "모든 필드를 입력해주세요.")
            return
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)', (num, name, now, now))
            self.conn.commit()
            self.load_students()
            self.num_edit.clear()
            self.name_edit.clear()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "오류", "이미 존재하는 학번입니다.")
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "오류", f"학생 추가 중 오류: {str(e)}")

    def update_student(self):
        if not hasattr(self, 'selected_student_number'):
            QMessageBox.warning(self, "경고", "수정할 학생을 선택해주세요.")
            return
        num = self.num_edit.text().strip()
        name = self.name_edit.text().strip()
        if not num or not name:
            QMessageBox.warning(self, "오류", "모든 필드를 입력해주세요.")
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.cursor.execute('UPDATE students SET student_number=?, name=?, last_modified=? WHERE student_number=?', (num, name, now, self.selected_student_number))
            self.conn.commit()
            self.load_students()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "오류", "이미 존재하는 학번입니다.")
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "오류", f"학생 정보 수정 중 오류: {str(e)}")

    def delete_student(self):
        if not hasattr(self, 'selected_student_number'):
            QMessageBox.warning(self, "경고", "삭제할 학생을 선택해주세요.")
            return
        try:
            self.cursor.execute('DELETE FROM students WHERE student_number=?', (self.selected_student_number,))
            self.conn.commit()
            self.load_students()
            self.eval_table.setRowCount(0)
            self.num_edit.clear()
            self.name_edit.clear()
            if hasattr(self, 'selected_student_number'):
                del self.selected_student_number
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "오류", f"학생 삭제 중 오류: {str(e)}")

    def load_evaluations(self):
        self.eval_table.setRowCount(0)
        self.cursor.execute('SELECT id FROM students WHERE student_number=?', (self.selected_student_number,))
        result = self.cursor.fetchone()
        if not result:
            return
        student_id = result[0]
        self.cursor.execute('SELECT subject, score, evaluation_date, notes FROM evaluations WHERE student_id=? ORDER BY evaluation_date DESC', (student_id,))
        for row in self.cursor.fetchall():
            row_pos = self.eval_table.rowCount()
            self.eval_table.insertRow(row_pos)
            for col, val in enumerate(row):
                self.eval_table.setItem(row_pos, col, QTableWidgetItem(str(val)))

    def add_evaluation(self):
        if not hasattr(self, 'selected_student_number'):
            QMessageBox.warning(self, "경고", "평가를 추가할 학생을 선택해주세요.")
            return
        subject = self.subject_edit.text().strip()
        score = self.score_edit.text().strip()
        eval_date = self.eval_date_edit.text().strip()
        notes = self.notes_edit.text().strip()
        if not subject or not score or not eval_date:
            QMessageBox.warning(self, "오류", "과목, 점수, 평가일을 입력해주세요.")
            return
        try:
            score_val = float(score)
        except ValueError:
            QMessageBox.warning(self, "오류", "점수는 숫자로 입력해주세요.")
            return
        if not is_valid_date(eval_date):
            QMessageBox.warning(self, "오류", "평가일은 YYYY-MM-DD 형식이어야 합니다.")
            return
        try:
            self.cursor.execute('SELECT id FROM students WHERE student_number=?', (self.selected_student_number,))
            result = self.cursor.fetchone()
            if not result:
                return
            student_id = result[0]
            self.cursor.execute('INSERT INTO evaluations (student_id, subject, score, evaluation_date, notes) VALUES (?, ?, ?, ?, ?)', (student_id, subject, score_val, eval_date, notes))
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('UPDATE students SET last_modified=? WHERE id=?', (now, student_id))
            self.conn.commit()
            self.load_evaluations()
            self.load_students()
            self.subject_edit.clear()
            self.score_edit.clear()
            self.eval_date_edit.setText(datetime.now().strftime('%Y-%m-%d'))
            self.notes_edit.clear()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "오류", f"평가 추가 중 오류: {str(e)}")

    def delete_evaluation(self):
        selected = self.eval_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "경고", "삭제할 평가를 선택해주세요.")
            return
        subject = self.eval_table.item(selected, 0).text()
        score = self.eval_table.item(selected, 1).text()
        eval_date = self.eval_table.item(selected, 2).text()
        self.cursor.execute('SELECT id FROM students WHERE student_number=?', (self.selected_student_number,))
        student_id = self.cursor.fetchone()[0]
        self.cursor.execute('DELETE FROM evaluations WHERE student_id=? AND subject=? AND score=? AND evaluation_date=?', (student_id, subject, score, eval_date))
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('UPDATE students SET last_modified=? WHERE id=?', (now, student_id))
        self.conn.commit()
        self.load_evaluations()
        self.load_students()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = StudentDatabase()
    win.show()
    sys.exit(app.exec_())