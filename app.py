import streamlit as st
import zipfile, io, re
import pandas as pd
from bs4 import BeautifulSoup

st.set_page_config(page_title="XML 키워드 검색기", page_icon="🔍", layout="wide")
st.title("🔍 XML ZIP 문서 키워드 검색기")

st.markdown("""
ZIP 파일 안의 XML 문서들을 모두 분석해 특정 키워드가 포함된 파일을 찾아줍니다.  
예: `ESG`, `반도체`, `안전`, `품질`, `지속가능`, `인권` 등 자유롭게 검색 가능  
""")

uploaded_file = st.file_uploader("📂 ZIP 파일 업로드", type=["zip"])
keywords_input = st.text_input("🔎 검색할 키워드 (쉼표로 구분 가능)", value="ESG")

if uploaded_file and keywords_input.strip():
    keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
    results = []

    with zipfile.ZipFile(uploaded_file, "r") as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".xml"):
                continue
            try:
                with zf.open(name) as fp:
                    text = fp.read().decode("utf-8", errors="ignore")
            except Exception:
                continue

            # BeautifulSoup으로 XML 파싱 및 텍스트 추출
            soup = BeautifulSoup(text, "xml")
            text_content = soup.get_text(" ", strip=True)

            found_words = []
            snippets = []

            for kw in keywords:
                pattern = re.compile(r".{0,50}" + re.escape(kw) + r".{0,50}", re.IGNORECASE)
                matches = pattern.findall(text_content)
                if matches:
                    found_words.append(kw)
                    for m in matches[:3]:  # 최대 3개까지만 미리보기
                        snippets.append(f"...{m}...")

            if found_words:
                results.append({
                    "파일명": name,
                    "일치 키워드": ", ".join(found_words),
                    "일치 횟수": len(snippets),
                    "문장 일부": "\n".join(snippets)
                })

    if results:
        df = pd.DataFrame(results)
        st.success(f"✅ 총 {len(df)}개 파일에서 키워드 발견")
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
    st.info("ZIP 파일을 업로드하고 검색할 키워드를 입력하세요.")
