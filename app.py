import streamlit as st
import zipfile, re, unicodedata
import pandas as pd
from bs4 import BeautifulSoup

# 선택적 인코딩 탐지
try:
    import chardet
except ImportError:
    chardet = None

# ------------------------------
# 페이지 설정
# ------------------------------
st.set_page_config(page_title="XML 키워드 검색기", page_icon="🔍", layout="wide")
st.title("🔍 XML ZIP 문서 키워드 검색기")

st.markdown("""
ZIP 파일 안의 XML/HTML 문서들을 분석해 **사용자가 입력한 키워드**가 포함된 문서를 찾아줍니다.  
예: `임원`, `ESG`, `품질`, `지속가능`, `반도체` 등 자유롭게 검색 가능  
""")

# ------------------------------
# 텍스트 추출 유틸리티
# ------------------------------
def try_decode(raw: bytes) -> str:
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

# ------------------------------
# UI 구성
# ------------------------------
uploaded_file = st.file_uploader("📂 ZIP 파일 업로드", type=["zip"])
keywords_input = st.text_input("🔎 검색할 키워드 (쉼표로 구분 가능)")

search_button = st.button("검색 시작 🔍")

# ------------------------------
# 검색 로직
# ------------------------------
if search_button:
    if not uploaded_file:
        st.warning("⚠️ ZIP 파일을 먼저 업로드하세요.")
    elif not keywords_input.strip():
        st.warning("⚠️ 검색할 키워드를 입력하세요.")
    else:
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        results = []
        targets = (".xml", ".xbrl", ".htm", ".html", ".txt")

        with zipfile.ZipFile(uploaded_file, "r") as zf:
            file_list = [n for n in zf.namelist() if n.lower().endswith(targets)]
            progress = st.progress(0, text="검색 중...")

            for i, name in enumerate(file_list, start=1):
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
                        "파일명": name,
                        "일치 키워드": ", ".join(found_words),
                        "일치 횟수": len(snippets),
                        "문장 일부": "\n".join(snippets)
                    })

                progress.progress(i / len(file_list), text=f"검색 중... ({i}/{len(file_list)})")

        # ------------------------------
        # 결과 표시
        # ------------------------------
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
