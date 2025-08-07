import sys
import sqlite3
from datetime import datetime
import csv
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView, QMessageBox,
    QMenuBar, QMenu, QFileDialog, QComboBox
)
from PySide6.QtGui import QKeySequence, QFont, QAction
from PySide6.QtCore import Qt
from config_manager import ConfigManager

# 상수 정의
DB_FILE = 'student.db'
CSV_HEADER = ["년도", "학번", "이름", "등록일", "최근평가일", "과목", "점수", "평가일", "비고"]

# 데이터 검증 함수들
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

def is_valid_student_number(student_number):
    """학번 형식 검증 (숫자만 허용, 4-10자리)"""
    if not student_number:
        return False
    pattern = r'^\d{4,10}$'
    return bool(re.match(pattern, student_number))

def is_valid_score(score_str):
    """점수 검증 (0-100 범위)"""
    try:
        score = float(score_str)
        return 0 <= score <= 100
    except ValueError:
        return False

def is_valid_name(name):
    """이름 검증 (1-20자, 한글/영문/숫자 허용)"""
    if not name:
        return False
    pattern = r'^[가-힣a-zA-Z0-9\s]{1,20}$'
    return bool(re.match(pattern, name))

class StudentDatabase(QWidget):
    def __init__(self):
        super().__init__()
        
        # 설정 관리자 초기화
        self.config_manager = ConfigManager()
        
        self.setWindowTitle("학생 관리 시스템 (PySide6)")
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
        
        
        # 설정에서 데이터베이스 경로 가져오기
        db_path = self.config_manager.get('database_path', 'student.db')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        # 외래키 제약조건 활성화
        self.cursor.execute('PRAGMA foreign_keys = ON')
        self.init_database()
        self.init_ui(font_size)
        self.load_students()
        self.refresh_statistics()  # 초기 통계 로드

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
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    def init_ui(self, font_size):
        main_layout = QVBoxLayout()

        # 메뉴바 추가 (폰트 크기 1.0배 적용)
        
        self.menubar = QMenuBar(self)
        menubar_font = QFont()
        menubar_font.setPointSizeF(font_size * 1.0)
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
        file_menu.addSeparator()
        backup_action = QAction("데이터베이스 백업", self)
        backup_action.setFont(menubar_font)
        backup_action.triggered.connect(self.backup_database)
        restore_action = QAction("데이터베이스 복원", self)
        restore_action.setFont(menubar_font)
        restore_action.triggered.connect(self.restore_database)
        file_menu.addAction(backup_action)
        file_menu.addAction(restore_action)
        self.menubar.addMenu(file_menu)
        
        # 설정 메뉴 추가
        settings_menu = QMenu("설정", self)
        settings_menu.setFont(menubar_font)
        settings_action = QAction("설정", self)
        settings_action.setFont(menubar_font)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)
        self.menubar.addMenu(settings_menu)
        main_layout.setMenuBar(self.menubar)
        self.setLayout(main_layout)

        # 학생 정보 입력
        input_group = QGroupBox("학생 정보")
        input_layout = QHBoxLayout()
        
        # 년도 선택 콤보박스
        self.year_combo = QComboBox()
        self.load_year_combo()
        
        self.num_edit = QLineEdit()
        self.name_edit = QLineEdit()
        
        # 년도 콤보박스의 가로폭을 학번 입력창과 동일하게 설정
        num_width = self.num_edit.sizeHint().width()
        self.year_combo.setFixedWidth(num_width)
        
        input_layout.addWidget(QLabel("년도:"))
        input_layout.addWidget(self.year_combo)
        input_layout.addWidget(QLabel("학번:"))
        input_layout.addWidget(self.num_edit)
        input_layout.addWidget(QLabel("이름:"))
        input_layout.addWidget(self.name_edit)
        input_layout.addStretch(1)  # 입력창 좌측 정렬
        
        self.add_btn = QPushButton("추가")
        self.update_btn = QPushButton("수정")
        self.delete_btn = QPushButton("삭제")
        # 버튼 가로폭을 2배로 늘림
        # 평가 버튼 가로폭을 기준으로 학생 정보 버튼 가로폭도 동일하게 맞춤
        eval_btn_width = QPushButton("평가 추가").sizeHint().width() * 2
        for btn in [self.add_btn, self.update_btn, self.delete_btn]:
            btn.setFixedWidth(eval_btn_width)
        input_layout.addWidget(self.add_btn)
        input_layout.addWidget(self.update_btn)
        input_layout.addWidget(self.delete_btn)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # 검색 기능
        search_group = QGroupBox("검색")
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("학생 검색 (학번, 이름)")
        self.search_edit.textChanged.connect(self.search_students)
        self.clear_search_btn = QPushButton("검색 초기화")
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.clear_search_btn)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # 통계 정보 표시
        stats_group = QGroupBox("통계 정보")
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("총 학생: 0명 | 총 평가: 0개 | 평균 점수: 0.0")
        self.refresh_stats_btn = QPushButton("통계 새로고침")
        self.refresh_stats_btn.clicked.connect(self.refresh_statistics)
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(self.refresh_stats_btn)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

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
        from PySide6.QtWidgets import QSizePolicy
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
        self.update_btn.clicked.connect(self.update_student)
        self.delete_btn.clicked.connect(self.delete_student)
        self.table.cellClicked.connect(self.on_student_select)
        self.table.cellDoubleClicked.connect(self.on_student_double_click)
        self.eval_add_btn.clicked.connect(self.add_evaluation)
        self.eval_delete_btn.clicked.connect(self.delete_evaluation)
        
        # 키보드 단축키 설정
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """키보드 단축키 설정"""
        # 학생 관리 단축키
        add_shortcut = QAction("학생 추가", self)
        add_shortcut.setShortcut(QKeySequence("Ctrl+N"))
        add_shortcut.triggered.connect(self.add_student)
        self.addAction(add_shortcut)
        
        update_shortcut = QAction("학생 수정", self)
        update_shortcut.setShortcut(QKeySequence("Ctrl+E"))
        update_shortcut.triggered.connect(self.update_student)
        self.addAction(update_shortcut)
        
        delete_shortcut = QAction("학생 삭제", self)
        delete_shortcut.setShortcut(QKeySequence("Delete"))
        delete_shortcut.triggered.connect(self.delete_student)
        self.addAction(delete_shortcut)
        
        # 평가 관리 단축키
        eval_add_shortcut = QAction("평가 추가", self)
        eval_add_shortcut.setShortcut(QKeySequence("Ctrl+A"))
        eval_add_shortcut.triggered.connect(self.add_evaluation)
        self.addAction(eval_add_shortcut)
        
        eval_delete_shortcut = QAction("평가 삭제", self)
        eval_delete_shortcut.setShortcut(QKeySequence("Ctrl+D"))
        eval_delete_shortcut.triggered.connect(self.delete_evaluation)
        self.addAction(eval_delete_shortcut)
        
        # 파일 관리 단축키
        export_shortcut = QAction("CSV 내보내기", self)
        export_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        export_shortcut.triggered.connect(self.export_csv)
        self.addAction(export_shortcut)
        
        import_shortcut = QAction("CSV 불러오기", self)
        import_shortcut.setShortcut(QKeySequence("Ctrl+O"))
        import_shortcut.triggered.connect(self.import_csv)
        self.addAction(import_shortcut)
        
        # 검색 단축키
        search_shortcut = QAction("검색", self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(lambda: self.search_edit.setFocus())
        self.addAction(search_shortcut)
        
        # 통계 새로고침 단축키
        stats_shortcut = QAction("통계 새로고침", self)
        stats_shortcut.setShortcut(QKeySequence("F5"))
        stats_shortcut.triggered.connect(self.refresh_statistics)
        self.addAction(stats_shortcut)

    def export_csv(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "학생정보 CSV 내보내기", "students.csv", "CSV Files (*.csv)", options=options)
        if file_path:
            try:
                # 학생 정보와 평가 정보를 통합하여 조회
                self.cursor.execute('''
                    SELECT 
                        SUBSTR(s.student_number, 1, 4) as year,
                        s.student_number, 
                        s.name, 
                        s.created_at, 
                        s.last_modified,
                        e.subject, 
                        e.score, 
                        e.evaluation_date, 
                        e.notes 
                    FROM students s 
                    LEFT JOIN evaluations e ON s.id = e.student_id 
                    ORDER BY s.student_number, e.evaluation_date DESC
                ''')
                data = self.cursor.fetchall()
                
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(CSV_HEADER)
                    writer.writerows(data)
                
                QMessageBox.information(self, "성공", f"학생정보와 평가정보가 통합 CSV로 저장되었습니다.\n\n파일: {file_path}")
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
                    data = list(reader)
                
                # 컬럼 검증
                if reader.fieldnames != CSV_HEADER:
                    QMessageBox.critical(self, "오류", f"CSV의 컬럼이 올바르지 않습니다.\n필요: {CSV_HEADER}\n입력: {reader.fieldnames}")
                    return
                
                self.cursor.execute('DELETE FROM evaluations')
                self.cursor.execute('DELETE FROM students')
                
                # 학생 정보와 평가 정보를 분리하여 처리
                students_added = set()  # 중복 학생 방지
                
                for row in data:
                    student_number = row["학번"]
                    
                    # 학생 정보가 아직 추가되지 않았다면 추가
                    if student_number not in students_added:
                        self.cursor.execute('INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)',
                            (student_number, row["이름"], row["등록일"], row["최근평가일"]))
                        students_added.add(student_number)
                    
                    # 평가 정보가 있다면 추가
                    if row["과목"] and row["점수"] and row["평가일"]:
                        self.cursor.execute('SELECT id FROM students WHERE student_number=?', (student_number,))
                        res = self.cursor.fetchone()
                        if res:
                            student_id = res[0]
                            # 점수 float 변환, 날짜 검증
                            score = None
                            try:
                                score = float(row["점수"]) if row["점수"] else None
                            except ValueError:
                                pass
                            eval_date = row["평가일"] if is_valid_date(row["평가일"]) else None
                            if score is not None and eval_date:
                                self.cursor.execute('INSERT INTO evaluations (student_id, subject, score, evaluation_date, notes) VALUES (?, ?, ?, ?, ?)',
                                    (student_id, row["과목"], score, eval_date, row["비고"]))
                
                self.conn.commit()
                self.load_students()
                self.load_year_combo()  # 년도 콤보박스 업데이트
                self.eval_table.setRowCount(0)
                QMessageBox.information(self, "성공", "통합 CSV에서 학생정보와 평가정보를 불러왔습니다.")
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "오류", f"CSV 불러오기 중 오류 발생: {str(e)}")

    def load_year_combo(self):
        """데이터베이스에서 실제 사용 중인 년도들을 조회하여 콤보박스에 추가"""
        self.year_combo.clear()
        
        # 데이터베이스에서 학번의 앞 4자리(년도)를 추출하여 중복 제거 후 정렬
        self.cursor.execute('''
            SELECT DISTINCT SUBSTR(student_number, 1, 4) as year 
            FROM students 
            WHERE LENGTH(student_number) >= 4 
            ORDER BY year
        ''')
        years = [row[0] for row in self.cursor.fetchall()]
        
        # 현재 년도가 없으면 추가
        current_year = str(datetime.now().year)
        if current_year not in years:
            years.append(current_year)
            years.sort()
        
        # 년도들을 콤보박스에 추가
        for year in years:
            self.year_combo.addItem(year)
        
        # 현재 년도를 기본값으로 설정
        self.year_combo.setCurrentText(current_year)

    def load_students(self, search_keyword=""):
        self.table.setRowCount(0)
        
        if search_keyword.strip():
            # 검색 조건이 있는 경우
            self.cursor.execute('''
                SELECT student_number, name, created_at, last_modified 
                FROM students 
                WHERE student_number LIKE ? OR name LIKE ?
                ORDER BY student_number
            ''', (f'%{search_keyword}%', f'%{search_keyword}%'))
        else:
            # 검색 조건이 없는 경우
            self.cursor.execute('SELECT student_number, name, created_at, last_modified FROM students ORDER BY student_number')
        
        for row in self.cursor.fetchall():
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            for col, val in enumerate(row):
                self.table.setItem(row_pos, col, QTableWidgetItem(str(val)))

    def search_students(self):
        """실시간 검색 기능"""
        search_keyword = self.search_edit.text().strip()
        self.load_students(search_keyword)

    def clear_search(self):
        """검색 초기화"""
        self.search_edit.clear()
        self.load_students()

    def on_student_double_click(self, row, col):
        """학생 더블클릭 시 수정 모드로 전환"""
        self.on_student_select(row, col)
        # 수정 버튼 클릭 효과
        self.update_btn.setFocus()
        QMessageBox.information(self, "수정 모드", "학생 정보를 수정하고 '수정' 버튼을 클릭하세요.")

    def backup_database(self):
        """데이터베이스 백업"""
        options = QFileDialog.Options()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"student_backup_{timestamp}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "데이터베이스 백업", default_name, 
            "SQLite Database (*.db)", options=options
        )
        if file_path:
            try:
                import shutil
                shutil.copy2('student.db', file_path)
                QMessageBox.information(self, "성공", f"데이터베이스가 백업되었습니다.\n\n파일: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"백업 중 오류 발생: {str(e)}")

    def restore_database(self):
        """데이터베이스 복원"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "데이터베이스 복원", "", 
            "SQLite Database (*.db)", options=options
        )
        if file_path:
            try:
                reply = QMessageBox.question(
                    self, "확인", 
                    "현재 데이터베이스를 백업 파일로 덮어쓰시겠습니까?\n현재 데이터가 모두 삭제됩니다.",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    import shutil
                    shutil.copy2(file_path, 'student.db')
                    # 데이터베이스 연결 재설정
                    self.conn.close()
                    self.conn = sqlite3.connect('student.db')
                    self.cursor = self.conn.cursor()
                    self.cursor.execute('PRAGMA foreign_keys = ON')
                    # UI 새로고침
                    self.load_students()
                    self.load_year_combo()
                    self.refresh_statistics()
                    QMessageBox.information(self, "성공", "데이터베이스가 복원되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"복원 중 오류 발생: {str(e)}")

    def refresh_statistics(self):
        """통계 정보 새로고침"""
        try:
            # 총 학생 수
            self.cursor.execute('SELECT COUNT(*) FROM students')
            total_students = self.cursor.fetchone()[0]
            
            # 총 평가 수
            self.cursor.execute('SELECT COUNT(*) FROM evaluations')
            total_evaluations = self.cursor.fetchone()[0]
            
            # 평균 점수
            self.cursor.execute('SELECT AVG(score) FROM evaluations WHERE score IS NOT NULL')
            avg_score_result = self.cursor.fetchone()[0]
            avg_score = avg_score_result if avg_score_result else 0.0
            
            # 통계 업데이트
            stats_text = f"총 학생: {total_students}명 | 총 평가: {total_evaluations}개 | 평균 점수: {avg_score:.1f}"
            self.stats_label.setText(stats_text)
        except Exception as e:
            self.stats_label.setText("통계 로드 중 오류 발생")

    def show_settings(self):
        """설정 창 표시"""
        from PySide6.QtWidgets import QDialog, QFormLayout, QCheckBox, QSpinBox, QComboBox, QLineEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("설정")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QFormLayout()
        
        # 데이터베이스 경로
        db_path_edit = QLineEdit(self.config_manager.get('database_path', 'student.db'))
        layout.addRow("데이터베이스 경로:", db_path_edit)
        
        # 자동 백업
        auto_backup_check = QCheckBox()
        auto_backup_check.setChecked(self.config_manager.get('backup_auto', True))
        layout.addRow("자동 백업:", auto_backup_check)
        
        # 백업 간격
        backup_interval_spin = QSpinBox()
        backup_interval_spin.setRange(1, 30)
        backup_interval_spin.setValue(self.config_manager.get('backup_interval', 7))
        layout.addRow("백업 간격 (일):", backup_interval_spin)
        
        # 기본 년도
        default_year_spin = QSpinBox()
        default_year_spin.setRange(2000, 2100)
        default_year_spin.setValue(self.config_manager.get('default_year', 2024))
        layout.addRow("기본 년도:", default_year_spin)
        
        # UI 테마
        theme_combo = QComboBox()
        theme_combo.addItems(["light", "dark"])
        theme_combo.setCurrentText(self.config_manager.get('ui_theme', 'light'))
        layout.addRow("UI 테마:", theme_combo)
        
        # 언어
        language_combo = QComboBox()
        language_combo.addItems(["ko", "en"])
        language_combo.setCurrentText(self.config_manager.get('language', 'ko'))
        layout.addRow("언어:", language_combo)
        
        # 자동 저장
        auto_save_check = QCheckBox()
        auto_save_check.setChecked(self.config_manager.get('auto_save', True))
        layout.addRow("자동 저장:", auto_save_check)
        
        # 실시간 검색
        search_auto_check = QCheckBox()
        search_auto_check.setChecked(self.config_manager.get('search_auto', True))
        layout.addRow("실시간 검색:", search_auto_check)
        
        # 통계 자동 새로고침
        stats_auto_check = QCheckBox()
        stats_auto_check.setChecked(self.config_manager.get('stats_auto_refresh', True))
        layout.addRow("통계 자동 새로고침:", stats_auto_check)
        
        # 단축키 활성화
        shortcuts_check = QCheckBox()
        shortcuts_check.setChecked(self.config_manager.get('shortcuts_enabled', True))
        layout.addRow("단축키 활성화:", shortcuts_check)
        
        # 버튼
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            # 설정 저장
            new_config = {
                'database_path': db_path_edit.text(),
                'backup_auto': auto_backup_check.isChecked(),
                'backup_interval': backup_interval_spin.value(),
                'default_year': default_year_spin.value(),
                'ui_theme': theme_combo.currentText(),
                'language': language_combo.currentText(),
                'auto_save': auto_save_check.isChecked(),
                'search_auto': search_auto_check.isChecked(),
                'stats_auto_refresh': stats_auto_check.isChecked(),
                'shortcuts_enabled': shortcuts_check.isChecked()
            }
            
            if self.config_manager.update(new_config):
                QMessageBox.information(self, "성공", "설정이 저장되었습니다.\n일부 설정은 애플리케이션 재시작 후 적용됩니다.")
            else:
                QMessageBox.warning(self, "오류", "설정 저장에 실패했습니다.")

    def on_student_select(self, row, col):
        self.selected_student_number = self.table.item(row, 0).text()
        
        # 학번에서 년도와 번호 분리
        if len(self.selected_student_number) >= 4:
            year = self.selected_student_number[:4]
            number = self.selected_student_number[4:]
            
            # 년도 콤보박스 설정
            index = self.year_combo.findText(year)
            if index >= 0:
                self.year_combo.setCurrentIndex(index)
            
            # 학번 입력창에 번호만 표시
            self.num_edit.setText(number)
        else:
            self.num_edit.setText(self.selected_student_number)
            
        self.name_edit.setText(self.table.item(row, 1).text())
        self.load_evaluations()

    def add_student(self):
        year = self.year_combo.currentText()
        num = self.num_edit.text().strip()
        name = self.name_edit.text().strip()
        
        # 입력 검증
        if not num or not name:
            QMessageBox.warning(self, "오류", "모든 필드를 입력해주세요.")
            return
        
        if not is_valid_student_number(num):
            QMessageBox.warning(self, "오류", "학번은 4-10자리 숫자로 입력해주세요.")
            return
            
        if not is_valid_name(name):
            QMessageBox.warning(self, "오류", "이름은 1-20자로 입력해주세요.")
            return
        
        # 년도와 학번을 결합하여 완전한 학번 생성
        full_student_number = year + num
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('INSERT INTO students (student_number, name, created_at, last_modified) VALUES (?, ?, ?, ?)', (full_student_number, name, now, now))
            self.conn.commit()
            self.load_students()
            self.load_year_combo()  # 년도 콤보박스 업데이트
            self.refresh_statistics()  # 통계 업데이트
            self.num_edit.clear()
            self.name_edit.clear()
            self.search_edit.clear()  # 검색 초기화
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "오류", "이미 존재하는 학번입니다.")
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "오류", f"학생 추가 중 오류: {str(e)}")

    def update_student(self):
        if not hasattr(self, 'selected_student_number'):
            QMessageBox.warning(self, "경고", "수정할 학생을 선택해주세요.")
            return
        year = self.year_combo.currentText()
        num = self.num_edit.text().strip()
        name = self.name_edit.text().strip()
        if not num or not name:
            QMessageBox.warning(self, "오류", "모든 필드를 입력해주세요.")
            return
        
        # 년도와 학번을 결합하여 완전한 학번 생성
        full_student_number = year + num
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.cursor.execute('UPDATE students SET student_number=?, name=?, last_modified=? WHERE student_number=?', (full_student_number, name, now, self.selected_student_number))
            self.conn.commit()
            self.load_students()
            self.load_year_combo()  # 년도 콤보박스 업데이트
            self.search_edit.clear()  # 검색 초기화
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
            self.load_year_combo()  # 년도 콤보박스 업데이트
            self.refresh_statistics()  # 통계 업데이트
            self.search_edit.clear()  # 검색 초기화
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
        
        # 입력 검증
        if not subject or not score or not eval_date:
            QMessageBox.warning(self, "오류", "과목, 점수, 평가일을 입력해주세요.")
            return
            
        if not is_valid_score(score):
            QMessageBox.warning(self, "오류", "점수는 0-100 사이의 숫자로 입력해주세요.")
            return
            
        if not is_valid_date(eval_date):
            QMessageBox.warning(self, "오류", "평가일은 YYYY-MM-DD 형식이어야 합니다.")
            return
        try:
            score_val = float(score)
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
            self.refresh_statistics()  # 통계 업데이트
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
    sys.exit(app.exec())