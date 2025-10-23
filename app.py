import streamlit as st
import zipfile, io, re, unicodedata
import pandas as pd
from bs4 import BeautifulSoup

# 선택적 인코딩 탐지
try:
    import chardet
except ImportError:
    chardet = None

# =============== 기본 설정 ===============
st.set_page_config(page_title="XML 키워드 검색기", page_icon="🔍", layout="wide")
st.title("🔍 XML ZIP 문서 키워드 검색기 (재귀 ZIP + DART 링크)")

st.markdown("""
업로드한 ZIP 파일(중첩 ZIP 포함)에서 XML/HTML/TXT를 분석해  
입력한 **키워드**가 포함된 문서를 찾고, 가능하면 **DART 원문 링크**까지 제공합니다.
""")

DART_BASE = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="

# =============== 유틸: 인코딩/텍스트 추출 ===============
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

# =============== 유틸: rcpNo(접수번호) 추출 ===============
_rcpno_pat = re.compile(r"(?:<rcept_no>\s*(20\d{12})\s*</rcept_no>)|(?:\b(20\d{12})\b)", re.IGNORECASE)

def find_rcpno_from_path(path: str) -> str | None:
    # 경로/파일명에서 14자리 접수번호 찾기 (2000년대 형식 가정)
    m = re.search(r"\b(20\d{12})\b", path)
    return m.group(1) if m else None

def find_rcpno_from_text(text: str) -> str | None:
    # <rcept_no>2023... </rcept_no> 또는 그냥 14자리 숫자
    m = _rcpno_pat.search(text)
    if not m:
        return None
    return m.group(1) or m.group(2)

def make_dart_link(rcpno: str | None) -> str:
    return f"{DART_BASE}{rcpno}" if rcpno else ""

# =============== 재귀 ZIP 탐색 ===============
def extract_texts_from_zip(zf_bytes, keywords, results, parent=""):
    try:
        with zipfile.ZipFile(io.BytesIO(zf_bytes), "r") as zf:
            for name in zf.namelist():
                path = f"{parent}/{name}" if parent else name

                # 내부 ZIP → 재귀
                if name.lower().endswith(".zip"):
                    try:
                        inner_bytes = zf.read(name)
                        extract_texts_from_zip(inner_bytes, keywords, results, parent=path)
                    except Exception:
                        continue

                # 대상 확장자
                elif name.lower().endswith((".xml", ".xbrl", ".htm", ".html", ".txt")):
                    try:
                        raw = zf.read(name)
                    except Exception:
                        continue

                    text_content = extract_text(raw)
                    if not text_content:
                        continue

                    # rcpNo 추출 (우선순위: 경로 → 본문)
                    rcpno = find_rcpno_from_path(path) or find_rcpno_from_text(text_content)
                    dart_link = make_dart_link(rcpno)

                    found_words, snippets = [], []
                    for kw in keywords:
                        pat = re.compile(r".{0,50}" + re.escape(kw) + r".{0,50}", re.IGNORECASE)
                        matches = pat.findall(text_content)
                        if matches:
                            found_words.append(kw)
                            for m in matches[:3]:
                                snippets.append(f"...{m}...")

                    if found_words:
                        results.append({
                            "파일경로": path,
                            "일치 키워드": ", ".join(sorted(set(found_words))),
                            "일치 횟수": len(snippets),
                            "문장 일부": "\n".join(snippets),
                            "DART링크": dart_link
                        })
    except zipfile.BadZipFile:
        pass

# =============== UI ===============
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
        try:
            file_bytes = uploaded_file.read()
            extract_texts_from_zip(file_bytes, keywords, results)
        except Exception as e:
            st.error(f"ZIP 처리 중 오류: {e}")

        if results:
            df = pd.DataFrame(results)

            st.success(f"✅ 총 {len(df)}개 문서에서 키워드 발견")
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "파일경로": st.column_config.TextColumn("파일 경로", width="medium"),
                    "일치 키워드": st.column_config.TextColumn("일치 키워드"),
                    "일치 횟수": st.column_config.NumberColumn("일치 횟수"),
                    "문장 일부": st.column_config.TextColumn("문장 일부", width="large"),
                    # ✅ 클릭 가능한 링크
                    "DART링크": st.column_config.LinkColumn("DART 보고서", display_text="바로보기")
                }
            )

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
