import streamlit as st
import zipfile, io, re
import pandas as pd
from bs4 import BeautifulSoup

st.title("📂 ESG 관련 보고서 탐색기")

keywords = ["ESG", "지속가능경영", "환경", "사회", "거버넌스",
            "sustainability", "environment", "social", "governance"]

uploaded_file = st.file_uploader("ZIP 파일을 업로드하세요", type=["zip"])

if uploaded_file:
    results = []
    with zipfile.ZipFile(uploaded_file, "r") as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".xml"):
                continue
            with zf.open(name) as fp:
                try:
                    text = fp.read().decode("utf-8", errors="ignore")
                except:
                    continue
                soup = BeautifulSoup(text, "xml")
                text_content = soup.get_text(" ", strip=True)
                found = [kw for kw in keywords if kw.lower() in text_content.lower()]
                if found:
                    # 키워드가 포함된 문장 일부 추출
                    snippet = ""
                    for kw in found:
                        m = re.search(r".{0,40}" + kw + r".{0,40}", text_content, re.IGNORECASE)
                        if m:
                            snippet += f"...{m.group(0)}..."
                    results.append({"파일명": name, "일치 키워드": ", ".join(found), "문장 일부": snippet})
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📊 결과 CSV 다운로드", data=csv, file_name="esg_검색결과.csv", mime="text/csv")
    else:
        st.warning("ESG 관련 키워드가 포함된 문서를 찾지 못했습니다.")
