import streamlit as st


def st_no_top_borders() -> None:
    st.markdown(
        """
            <style>
                .block-container {
                    padding-top: 1.2rem !important;
                }
            </style>
        """,
        unsafe_allow_html=True,
    )


def button_page(page_url: str) -> str:
    return """
        <script type="text/javascript">
            function openInNewTab(url) {
                var win = window.open(url, '_blank');
                win.focus();
            }
        </script>

        <button onclick="openInNewTab('https://docs.python.org/3/library/asyncio-eventloop.html')">Открыть Streamlit страницу в новой вкладке</button>
    """
