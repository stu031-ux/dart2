# 🔍 XML ZIP 문서 키워드 검색기 (재귀 ZIP + DART 링크)

Streamlit 기반의 **XML ZIP 문서 키워드 검색기**입니다.  
업로드한 **ZIP 파일(중첩 ZIP 포함)** 안의 XML, HTML, TXT 문서를 분석하여  
입력한 **키워드**가 포함된 문서를 찾아주고, **DART 보고서 링크**를 자동 생성합니다.

---

## 🚀 주요 기능

### 📂 ZIP 파일 탐색
- **ZIP 안의 ZIP**(중첩 압축)까지 자동 탐색  
- `.xml`, `.xbrl`, `.html`, `.htm`, `.txt` 파일을 모두 분석  
- `<script>`, `<style>` 태그 자동 제거로 불필요한 내용 제외

### 🧠 인코딩 감지
- `utf-8`, `cp949`, `euc-kr` 기본 시도 후 실패 시 `chardet`로 자동 감지  
- 깨진 문자 최소화 및 유니코드 정규화(`NFKC`) 수행

### 🔎 키워드 검색
- 쉼표(`,`)로 구분된 다중 키워드 입력 가능  
  예: `임원, ESG, 지속가능, 품질`  
- 키워드 주변 ±50자 문맥 스니펫 표시  
- 키워드별 일치 횟수 및 요약 스니펫 표시

### 🧾 DART 보고서 링크 생성
- 파일명 또는 본문 내 **14자리 접수번호(20xxxxxxxxxxxx)** 자동 추출  
- `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=` 형태의 링크 자동 생성

### 📊 결과 출력 및 다운로드
- Streamlit 표로 결과 표시  
  (열: 파일 경로, 일치 키워드, 일치 횟수, 문장 일부, DART 링크)  
- **결과 CSV 다운로드** 버튼 제공 (`keyword_search_results.csv`)

---

## ⚙️ 설치 및 실행 방법

### 1️⃣ 필수 패키지 설치
```bash
pip install streamlit pandas beautifulsoup4 lxml chardet
```

### 2️⃣ 앱 실행
```bash
streamlit run app.py
```

### 3️⃣ 웹 브라우저에서 사용
1. **ZIP 파일 업로드**  
2. **검색할 키워드 입력**  
3. **검색 시작 버튼 클릭**  
4. 결과 표 및 DART 링크 확인  
5. CSV로 결과 다운로드

---

## 📁 폴더 구조 예시

```
📦 xml_keyword_searcher
 ┣ 📜 app.py
 ┣ 📜 README.md
 ┗ 📜 requirements.txt
```

---

## 🧩 코드 구성 요약

| 구분 | 함수명 | 설명 |
|------|---------|------|
| 🔤 인코딩 복원 | `try_decode()` | 다양한 인코딩을 시도해 텍스트 복원 |
| 🧾 텍스트 추출 | `extract_text()` | BeautifulSoup으로 본문만 추출 |
| 🔢 접수번호 식별 | `find_rcpno_from_path()` / `find_rcpno_from_text()` | DART 접수번호 자동 인식 |
| 🔁 ZIP 탐색 | `extract_texts_from_zip()` | ZIP 내부 ZIP까지 재귀 탐색 |
| 🌐 링크 생성 | `make_dart_link()` | DART 링크 자동 생성 |

---

## 💡 참고 사항
- 대용량 ZIP 파일은 처리 시간이 다소 소요될 수 있습니다.  
- 일부 비표준 XML 문서는 텍스트가 완전히 추출되지 않을 수 있습니다.  
- `chardet` 패키지는 선택사항이지만, 인코딩 오류 방지를 위해 설치를 권장합니다.

---

## 🏷️ 라이선스
이 코드는 자유롭게 수정 및 재배포 가능합니다.  
단, 상업적 이용 시 원 저작자 표시를 권장합니다.

---

**Made with ❤️ using [Streamlit](https://streamlit.io/)**
