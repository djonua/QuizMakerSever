import streamlit as st
from typing import Optional, Callable
from ..state.app_state import AppState, ArticleState

class ArticleView:
    """Component for displaying an article"""
    
    def __init__(self, supabase=None, on_generate_quiz: Optional[Callable] = None):
        self.supabase = supabase
        self.on_generate_quiz = on_generate_quiz
    
    def show_article(self, article: ArticleState):
        """Display article with quiz generation button"""
        if not article.content:
            return
            
        # Initialize expander state if it doesn't exist
        if 'article_expanded' not in st.session_state:
            st.session_state.article_expanded = True
            
        with st.expander("Article Text", expanded=st.session_state.article_expanded):
            st.markdown(article.content)
            
            if article.content:
                st.markdown("---")  # Разделитель перед кнопкой
                if st.button("Generate Quiz",
                        key="generate_quiz_btn",
                        use_container_width=True):
                    if self.on_generate_quiz:
                        # Collapse article before generating quiz
                        st.session_state.article_expanded = False
                        self.on_generate_quiz()
                        
    def delete_article(self, article_id: int):
        """Delete article from history"""
        try:
            self.supabase.table("article_history").delete().eq("id", article_id).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting article: {str(e)}")

    def show_article_history(self):
        """Show article history"""
        try:
            # Load article history
            result = self.supabase.table("article_history").select("*").order("created_at", desc=True).execute()
            articles = result.data if result and hasattr(result, 'data') else []
            
            if not articles:
                st.info("No articles in history")
                return
            
            # Display each article
            for article in articles:
                with st.container():
                    col1, col2, col3 = st.columns([6, 2, 2])
                    
                    # Article title
                    with col1:
                        title = article.get("title", "")
                        if len(title) > 50:
                            title = title[:47] + "..."
                        st.write(title)
                    
                    # Use button
                    with col2:
                        if st.button("Use this", key=f"use_{article['id']}"):
                            st.session_state.article = article
                            st.rerun()
                    
                    # Delete button
                    with col3:
                        if st.button("🗑️", key=f"delete_{article['id']}"):
                            self.delete_article(article['id'])
        except Exception as e:
            st.error(f"Error loading history: {str(e)}")
