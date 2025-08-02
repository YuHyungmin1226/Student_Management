# 🎓 Student Management - 학생 관리 시스템

**Student Management**는 PyQt5와 SQLite를 사용하여 개발된 완전한 학생 관리 시스템입니다. 학생 정보와 평가 기록을 체계적으로 관리할 수 있는 GUI 애플리케이션입니다.

## ✨ 주요 기능

### 👥 학생 정보 관리
- **학생 등록/수정/삭제**: 학번과 이름을 통한 학생 정보 관리
- **자동 타임스탬프**: 등록일과 최근 수정일 자동 기록
- **중복 학번 방지**: 유니크 제약으로 데이터 무결성 보장

### 📊 평가 기록 관리
- **과목별 평가**: 과목, 점수, 평가일, 비고 관리
- **실시간 업데이트**: 평가 추가/삭제 시 자동 반영
- **평가 이력 추적**: 학생별 평가 기록 조회

### 💾 데이터 관리
- **SQLite 데이터베이스**: 안정적이고 가벼운 데이터 저장
- **CSV 내보내기/가져오기**: 표준 형식으로 데이터 교환
- **UTF-8 인코딩**: 한글 완벽 지원

### 🖥️ 사용자 인터페이스
- **PyQt5 GUI**: 현대적이고 직관적인 인터페이스
- **반응형 디자인**: 화면 크기에 따른 자동 조정
- **화면 중앙 정렬**: 자동으로 최적 위치에 배치

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/YuHyungmin1226/Student_Management.git
cd Student_Management
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 실행
```bash
python student_database.py
```

## 📋 시스템 요구사항

- **Python**: 3.7 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 100MB
- **저장공간**: 최소 50MB

## 🗄️ 데이터베이스 구조

### Students 테이블
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_number TEXT UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Evaluations 테이블
```sql
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject TEXT NOT NULL,
    score REAL,
    evaluation_date DATE,
    notes TEXT,
    FOREIGN KEY (student_id) REFERENCES students (id)
);
```

## 📁 파일 구조

```
Student_Management/
├── student_database.py    # 메인 애플리케이션
├── requirements.txt       # Python 의존성
├── README.md             # 프로젝트 문서
├── .gitignore            # Git 무시 파일
├── build/                # 빌드 스크립트
│   └── build.py         # 자동 빌드 스크립트
└── tests/                # 테스트 파일
    └── test_student_db.py
```

## 🎯 사용 방법

### 학생 추가
1. **학번**과 **이름** 입력
2. **추가** 버튼 클릭
3. 학생 목록에 자동 추가됨

### 평가 추가
1. 학생 목록에서 **학생 선택**
2. **과목**, **점수**, **평가일**, **비고** 입력
3. **평가 추가** 버튼 클릭

### 데이터 내보내기
1. **파일 > CSV 내보내기** 메뉴 선택
2. 저장 위치 지정
3. 학생정보.csv와 평가정보.csv 파일 생성

### 데이터 가져오기
1. **파일 > CSV 불러오기** 메뉴 선택
2. 학생정보.csv 파일 선택
3. 기존 데이터 대체됨

## 🏗️ 빌드

PyInstaller를 사용하여 독립 실행형 애플리케이션을 빌드할 수 있습니다:

```bash
# Windows
pyinstaller --onefile --noconsole --name "StudentManagement" student_database.py

# macOS
pyinstaller --onefile --windowed --name "StudentManagement" student_database.py

# Linux
pyinstaller --onefile --name "StudentManagement" student_database.py
```

## 🔧 설정

### 화면 크기 조정
- 애플리케이션은 화면 크기의 80%로 자동 설정
- 폰트 크기는 해상도에 따라 자동 조정

### 데이터베이스 위치
- 기본 위치: `student.db` (애플리케이션과 동일 폴더)
- SQLite 데이터베이스 파일

## 🐛 문제 해결

### 일반적인 문제
1. **PyQt5 설치 오류**: `pip install PyQt5` 명령어로 재설치
2. **데이터베이스 접근 오류**: 파일 권한 확인
3. **한글 깨짐**: UTF-8 인코딩 확인

### 로그 확인
- 애플리케이션 실행 시 콘솔에 오류 메시지 출력
- 데이터베이스 파일 손상 시 `student.db` 파일 삭제 후 재생성

## 📊 기능 상세

### 학생 관리
- ✅ 학생 등록 (학번, 이름)
- ✅ 학생 정보 수정
- ✅ 학생 삭제 (평가 기록도 함께 삭제)
- ✅ 학생 목록 조회

### 평가 관리
- ✅ 평가 추가 (과목, 점수, 날짜, 비고)
- ✅ 평가 삭제
- ✅ 학생별 평가 목록 조회
- ✅ 평가일 자동 업데이트

### 데이터 관리
- ✅ CSV 형식 내보내기
- ✅ CSV 형식 가져오기
- ✅ 데이터 검증 (날짜 형식, 필수 필드)
- ✅ UTF-8 인코딩 지원

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 개발자

**YuHyungmin1226** - [GitHub](https://github.com/YuHyungmin1226)

## 🔄 최근 업데이트

- ✅ **2025-01-XX**: 별도 저장소로 분리
- ✅ **2025-01-XX**: README.md 완전 최신화
- ✅ **2025-01-XX**: 빌드 스크립트 추가
- ✅ **2025-01-XX**: 테스트 파일 추가

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! 