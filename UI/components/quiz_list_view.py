import streamlit as st
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class QuizListView:
    """Component for displaying a list of quizzes"""
    
    def __init__(self, supabase):
        self.supabase = supabase
        if 'selected_test' not in st.session_state:
            st.session_state.selected_test = None
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0
            
        # Add styles once during initialization
        st.markdown("""
            <style>
            .quiz-card {
                border: 2px solid #e6e6e6;
                border-radius: 8px;
                padding: 0.8rem;
                margin-bottom: 0.8rem;
                background-color: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .quiz-card h3 {
                margin-top: 0;
                margin-bottom: 0.5rem;
            }
            /* Styles for buttons */
            .stButton {
                margin: 0 !important;
                padding: 0 !important;
            }
            .stButton button {
                padding: 0.3rem 0.5rem !important;
                height: auto !important;
                line-height: 1.2 !important;
                min-height: unset !important;
                font-size: 1.1rem !important;
            }
            /* Styles for card container */
            [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
                margin-top: 0.5rem !important;
                margin-bottom: 0 !important;
            }
            </style>
        """, unsafe_allow_html=True)
    
    def delete_test(self, test_id: str):
        """Delete test"""
        try:
            # First delete all questions
            self.supabase.table("questions").delete().eq("test_id", test_id).execute()
            
            # Then delete the test
            self.supabase.table("tests").delete().eq("id", test_id).execute()
            st.success("Test deleted successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting test: {str(e)}")
    
    def _format_date(self, date_str: str) -> str:
        """Format a date string"""
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date.strftime("%d.%m.%Y")
        except:
            return date_str
    
    def show_test_card(self, test: Dict):
        """Display a quiz card"""
        with st.container():
            # Create a style for the card
            st.markdown("""
                <style>
                .stButton button {
                    width: 100%;
                    padding: 0.5rem;
                    margin: 0.2rem 0;
                }
                .quiz-code {
                    font-family: monospace;
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #0066cc;
                    background-color: #f0f2f6;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    letter-spacing: 2px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Create the card
            with st.container():
                # Header and main information
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {test.get('title', 'Untitled Quiz')}")
                    
                    # Display the test code prominently
                    access_code = test.get('access_code', '')
                    if access_code:
                        st.markdown(f"""
                            <div style="margin: 10px 0;">
                                <span style="font-size: 0.9em; color: #666;">Test code:</span><br>
                                <span class="quiz-code">{access_code}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown(f"**Level:** {test.get('language_level', 'N/A')}")
                    st.markdown(f"**Created:** {self._format_date(test.get('created_at', ''))}")
                
                # Action buttons
                with col2:
                    if st.button("👁 View", key=f"view_{test['id']}"):
                        st.session_state.selected_test = test["id"]
                        st.session_state.edit_mode = False
                        st.rerun()
                        
                    if st.button("✏️ Edit", key=f"edit_{test['id']}"):
                        st.session_state.selected_test = test["id"]
                        st.session_state.edit_mode = True
                        st.rerun()
                        
                    if st.button("🗑️ Delete", key=f"delete_{test['id']}"):
                        self.delete_test(test['id'])
            
            # Horizontal line between cards
            st.markdown("---")
    
    def show_tests(self):
        """Display a list of quizzes"""
        try:
            st.title("My Quizzes")
            
            # Filters and search
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                level_filter = st.selectbox(
                    "Filter by Level",
                    ["All Levels", "A1", "A2", "B1", "B2", "C1", "C2", "original"]
                )
            with col2:
                search_query = st.text_input("🔍 Search quizzes", 
                                           placeholder="Enter quiz title...",
                                           key="quiz_search")
            
            st.markdown("---")
            
            # Pagination settings
            page_size = 10
            
            # Load quizzes with filter and pagination
            query = self.supabase.table("tests").select("*").order("created_at", desc=True)
            
            # Apply level filter if not "All Levels"
            if level_filter != "All Levels":
                query = query.eq("language_level", level_filter.lower())
                
            # Apply search filter if search query is not empty
            if search_query:
                # Используем ilike для поиска без учета регистра
                query = query.ilike("title", f"%{search_query}%")
                
            # Get total count for pagination
            count_result = query.execute()
            total_items = len(count_result.data if count_result and hasattr(count_result, 'data') else [])
            total_pages = (total_items + page_size - 1) // page_size
            
            # Apply pagination
            start = st.session_state.current_page * page_size
            query = query.range(start, start + page_size - 1)
            result = query.execute()
            tests = result.data if result and hasattr(result, 'data') else []
            
            if not tests:
                st.info("No tests found")
                return
            
            # Display quiz cards in two columns
            for i in range(0, len(tests), 2):
                col1, col2 = st.columns(2)
                with col1:
                    if tests[i]:
                        self.show_test_card(tests[i])
                with col2:
                    if i + 1 < len(tests) and tests[i + 1]:
                        self.show_test_card(tests[i + 1])
            
            # Pagination controls
            if total_pages > 1:
                st.markdown("---")
                cols = st.columns([1, 3, 1])
                with cols[0]:
                    if st.session_state.current_page > 0:
                        if st.button("← Previous"):
                            st.session_state.current_page -= 1
                            st.rerun()
                with cols[1]:
                    st.write(f"Page {st.session_state.current_page + 1} of {total_pages}")
                with cols[2]:
                    if st.session_state.current_page < total_pages - 1:
                        if st.button("Next →"):
                            st.session_state.current_page += 1
                            st.rerun()
                
        except Exception as e:
            st.error(f"Error loading tests: {str(e)}")
