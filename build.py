#!/usr/bin/env python3
"""
Student Management 빌드 스크립트
PyInstaller를 사용하여 독립 실행형 애플리케이션을 빌드합니다.
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

def clean_build_dirs():
    """빌드 디렉토리 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 {dir_name} 디렉토리 정리 중...")
            shutil.rmtree(dir_name)
    
    # .spec 파일 정리
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        print(f"🧹 {spec_file} 파일 삭제 중...")
        os.remove(spec_file)

def build_application():
    """애플리케이션 빌드"""
    print("🚀 Student Management 빌드 시작...")
    
    # PyInstaller 명령어 구성
    cmd = [
        'pyinstaller',
        '--onefile',                    # 단일 실행 파일
        '--noconsole',                  # 콘솔 창 숨김 (Windows)
        '--name=StudentManagement',     # 실행 파일 이름
        '--icon=icon.ico',              # 아이콘 (있는 경우)
        '--add-data=config.json;.',     # 설정 파일 포함
        '--hidden-import=PyQt5.sip',    # PyQt5 숨겨진 임포트
        '--hidden-import=sqlite3',      # SQLite 숨겨진 임포트
        '--clean',                      # 빌드 캐시 정리
        'student_database.py'           # 메인 파일
    ]
    
    # 아이콘이 없으면 제거
    if not os.path.exists('icon.ico'):
        cmd.remove('--icon=icon.ico')
    
    print("📦 빌드 명령어:", ' '.join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 빌드 성공!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        print(f"오류 출력: {e.stderr}")
        return False

def create_distribution():
    """배포 패키지 생성"""
    print("📦 배포 패키지 생성 중...")
    
    # dist 디렉토리 확인
    if not os.path.exists('dist'):
        print("❌ dist 디렉토리가 없습니다.")
        return False
    
    # 배포 폴더 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dist_folder = f"StudentManagement_v1.0_{timestamp}"
    
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    
    os.makedirs(dist_folder)
    
    # 실행 파일 복사
    exe_file = 'dist/StudentManagement.exe'
    if os.path.exists(exe_file):
        shutil.copy2(exe_file, dist_folder)
        print(f"✅ 실행 파일 복사: {exe_file}")
    else:
        print(f"❌ 실행 파일을 찾을 수 없습니다: {exe_file}")
        return False
    
    # README 파일 복사
    if os.path.exists('README.md'):
        shutil.copy2('README.md', dist_folder)
        print("✅ README.md 복사")
    
    # 설정 파일 복사
    if os.path.exists('config.json'):
        shutil.copy2('config.json', dist_folder)
        print("✅ config.json 복사")
    
    # requirements.txt 복사
    if os.path.exists('requirements.txt'):
        shutil.copy2('requirements.txt', dist_folder)
        print("✅ requirements.txt 복사")
    
    print(f"🎉 배포 패키지 생성 완료: {dist_folder}")
    return dist_folder

def main():
    """메인 빌드 프로세스"""
    print("=" * 50)
    print("🎓 Student Management 빌드 도구")
    print("=" * 50)
    
    # 1. 빌드 디렉토리 정리
    print("\n1️⃣ 빌드 디렉토리 정리...")
    clean_build_dirs()
    
    # 2. 애플리케이션 빌드
    print("\n2️⃣ 애플리케이션 빌드...")
    if not build_application():
        print("❌ 빌드가 실패했습니다.")
        return False
    
    # 3. 배포 패키지 생성
    print("\n3️⃣ 배포 패키지 생성...")
    dist_folder = create_distribution()
    if not dist_folder:
        print("❌ 배포 패키지 생성이 실패했습니다.")
        return False
    
    # 4. 빌드 완료
    print("\n" + "=" * 50)
    print("🎉 빌드 완료!")
    print("=" * 50)
    print(f"📁 배포 폴더: {dist_folder}")
    print(f"📄 실행 파일: {dist_folder}/StudentManagement.exe")
    print("\n💡 사용 방법:")
    print("1. 배포 폴더의 모든 파일을 원하는 위치에 복사")
    print("2. StudentManagement.exe 실행")
    print("3. config.json 파일로 설정 변경 가능")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 