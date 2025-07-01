import threading
from typing import Iterable, Tuple
import gradio as gr
import time

# Lock to handle concurrency safely
login_lock = threading.Lock()
current_user = None
user_expiration_time = 0

EXPIRATION_DURATION = 60 * 60  # Set expiration duration to 1 hour

def wrap_with_login_guard(demo):
    with gr.Blocks() as guarded_demo:

        init_btn = gr.Button("Start using Forge UI...")

        # Logged out message
        logged_out_view = gr.Column(visible=False)
        with logged_out_view:
            global current_user, user_expiration_time
            with login_lock:
                logged_out_markdown = gr.Markdown(f"## 🚪 You are logged out, or {current_user} is using the app.")

        # App interface      
        app_view = gr.Column(visible=False)
        with app_view:          
            footer_view = gr.Row()
            demo.render()  # Reuse the instantiated app inside the wrapper            
            with footer_view:
                username_display = gr.Markdown(scale=0)
                button_row = gr.Row(variant="compact")  # Create a compact row for buttons
                with button_row:
                    renew_btn = gr.Button("Renew", scale=1)  # Buttons will take minimal space within this row
                    logout_btn = gr.Button("Logout", scale=1)

        # Initialization logic to check username and conditionally render
        def check_user(request: gr.Request):
            global current_user, user_expiration_time
            with login_lock:
                username = request.username if request.username else "Unknown User"
                print(f"check_user {username} {current_user}")
                current_time = time.time()

                if username == current_user or current_user is None or current_time > user_expiration_time :
                    # Normal login logic
                    current_user = username
                    user_expiration_time = current_time + EXPIRATION_DURATION
                    expiration:str = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(user_expiration_time))
                    return gr.update(visible=False), gr.update(visible=True), f"## ✅ Logged in as: {username} until {expiration}", gr.update(visible=False), "", gr.update(value=str(user_expiration_time))

                else:
                    expiration:str = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(user_expiration_time))
                    return gr.update(visible=True), gr.update(visible=False), "", gr.update(visible=True), f"## 🚪 User '{current_user}' is using the app until {expiration}.", gr.update(value=str(user_expiration_time))

        def logout():
            global current_user, user_expiration_time
            with login_lock:
                current_user = None
                user_expiration_time = 0
            return gr.update(visible=True), gr.update(visible=False), "", gr.update(visible=True), f"## 🚪 You are logged out.", gr.update(value=str(user_expiration_time))

        init_btn.click(check_user, inputs=None, outputs=[logged_out_view, app_view, username_display, init_btn, logged_out_markdown], queue=False)
        renew_btn.click(check_user, inputs=None, outputs=[logged_out_view, app_view, username_display, init_btn, logged_out_markdown], queue=False)
        logout_btn.click(logout, inputs=None, outputs=[logged_out_view, app_view, username_display, init_btn, logged_out_markdown], queue=False)

        gr.Timer(value=300, repeat=True).tick( 
            fn=check_expiration_periodically,
            inputs=None,
            outputs=[logged_out_view, app_view, username_display, init_btn, logged_out_markdown]
        )

    return guarded_demo

def check_expiration_periodically():
    global current_user, user_expiration_time    
    with login_lock:        
        now = time.time()      
        if current_user and now > user_expiration_time:
            current_user = None
            user_expiration_time = 0
            return (
                gr.update(visible=True),    # logged_out_view
                gr.update(visible=False),   # app_view
                "⚠️ Session expired",       # username_display
                gr.update(visible=True),    # init_btn
                "## 🚪 Session expired.",   # logged_out_markdown
            )
        else:
            return (
                gr.skip(), 
                gr.skip(),
                gr.skip(),
                gr.skip(), 
                gr.skip(),
            )