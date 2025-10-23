import streamlit as st
import zipfile, io, re, unicodedata
import pandas as pd
from bs4 import BeautifulSoup

# 선택적 인코딩 탐지 라이브러리
try:
    import chardet
except ImportError:
    chardet = None

# ----------------------------------
# 기본 설정
# ----------------------------------
st.set_page_config(page_title="XML 키워드 검색기", page_icon="🔍", layout="wide")
st.title("🔍 XML ZIP 문서 키워드 검색기 (재귀 ZIP 지원 버전)")

st.markdown("""
업로드한 ZIP 파일 안의 XML/HTML 문서를 모두 분석해,  
**입력한 키워드가 포함된 문서**를 찾아 표시합니다.  
(※ ZIP 안에 또 ZIP이 들어있어도 모두 자동 탐색합니다)
""")

# ----------------------------------
# 텍스트 추출 함수
# ----------------------------------
def try_decode(raw: bytes) -> str:
    """여러 인코딩 시도로 안전하게 문자열 디코딩"""
    for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    if chardet:
        det = chardet.detect(raw)
        enc = (det.get("encoding") or "").lower()
        if enc:
            try:
                return raw.decode(enc, errors="replace")
            except Exception:
                pass
    return raw.decode("utf-8", errors="replace")

def extract_text(file_bytes: bytes) -> str:
    """XML/HTML/TXT 등에서 텍스트를 추출"""
    txt = try_decode(file_bytes)
    soup = None
    for parser in ("lxml-xml", "lxml", "html.parser"):
        try:
            soup = BeautifulSoup(txt, parser)
            if soup and soup.text.strip():
                break
        except Exception:
            continue
    if not soup:
        return ""
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ----------------------------------
# 재귀 ZIP 탐색 함수
# ----------------------------------
def extract_texts_from_zip(zf_bytes, keywords, results, parent=""):
    """ZIP 파일 내부의 XML/HTML 파일과 중첩 ZIP까지 재귀 탐색"""
    try:
        with zipfile.ZipFile(io.BytesIO(zf_bytes), "r") as zf:
            for name in zf.namelist():
                path = f"{parent}/{name}" if parent else name
                # 내부 ZIP 재귀 탐색
                if name.lower().endswith(".zip"):
                    try:
                        inner_bytes = zf.read(name)
                        extract_texts_from_zip(inner_bytes, keywords, results, parent=path)
                    except Exception:
                        continue
                # XML/HTML 파일 텍스트 추출
                elif name.lower().endswith((".xml", ".xbrl", ".htm", ".html", ".txt")):
                    try:
                        raw = zf.read(name)
                    except Exception:
                        continue
                    text_content = extract_text(raw)
                    if not text_content:
                        continue

                    found_words, snippets = [], []
                    for kw in keywords:
                        pattern = re.compile(r".{0,50}" + re.escape(kw) + r".{0,50}", re.IGNORECASE)
                        matches = pattern.findall(text_content)
                        if matches:
                            found_words.append(kw)
                            for m in matches[:3]:
                                snippets.append(f"...{m}...")

                    if found_words:
                        results.append({
                            "파일경로": path,
                            "일치 키워드": ", ".join(found_words),
                            "일치 횟수": len(snippets),
                            "문장 일부": "\n".join(snippets)
                        })
    except zipfile.BadZipFile:
        pass

# ----------------------------------
# Streamlit UI
# ----------------------------------
uploaded_file = st.file_uploader("📂 ZIP 파일 업로드", type=["zip"])
keywords_input = st.text_input("🔎 검색할 키워드 (쉼표로 구분 가능)", placeholder="예: 임원, ESG, 품질, 지속가능")

search_button = st.button("검색 시작 🔍")

if search_button:
    if not uploaded_file:
        st.warning("⚠️ ZIP 파일을 먼저 업로드하세요.")
    elif not keywords_input.strip():
        st.warning("⚠️ 검색할 키워드를 입력하세요.")
    else:
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        results = []
        progress = st.progress(0, text="ZIP 구조 탐색 중...")

        try:
            file_bytes = uploaded_file.read()
            extract_texts_from_zip(file_bytes, keywords, results)
        except Exception as e:
            st.error(f"ZIP 파일을 읽는 중 오류 발생: {e}")

        # ----------------------------------
        # 결과 표시
        # ----------------------------------
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ 총 {len(df)}개 문서에서 키워드 발견")
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📊 결과 CSV 다운로드",
                data=csv,
                file_name="keyword_search_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("❌ 일치하는 키워드가 포함된 문서를 찾지 못했습니다.")
else:
    st.info("ZIP 파일을 업로드하고 키워드를 입력한 뒤 **[검색 시작]** 버튼을 누르세요.")
