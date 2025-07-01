
import threading
from typing import Iterable, Tuple
import gradio as gr

# Lock to handle concurrency safely
login_lock = threading.Lock()
current_user = None


def wrap_with_login_guard(demo):
    with gr.Blocks() as guarded_demo:
    
        init_btn = gr.Button("Start using Forge UI...")

        # Logged out message
        logged_out_view = gr.Column(visible=False)
        with logged_out_view:
            gr.Markdown("## 🚪 You are logged out, or someone else is using the app.")

        # App interface
        app_view = gr.Column(visible=False)
        with app_view:
            username_display = gr.Markdown()
            demo.render()  # Reuse the instantiated app inside the wrapper
            logout_btn = gr.Button("Logout")

        # Initialization logic to check username and conditionally render
        def check_user(request: gr.Request):   
            global current_user
            with login_lock:         
                username = request.username if request.username else "Unknown User"
                print(f"check_user {username} {current_user}")
                if username == current_user or current_user is None:
                    current_user = username
                    return gr.update(visible=False), gr.update(visible=True), f"## ✅ Logged in as: {username}", gr.update(visible=False)
                else:
                    return gr.update(visible=True), gr.update(visible=False), "", gr.update(visible=True)
                
        def logout():
            global current_user
            with login_lock:     
                current_user = None
            return gr.update(visible=True), gr.update(visible=False), "", gr.update(visible=True)

        
        init_btn.click(check_user, inputs=None, outputs=[logged_out_view, app_view, username_display, init_btn], queue=False)
        logout_btn.click(logout, inputs=None, outputs=[logged_out_view, app_view, username_display, init_btn], queue=False)

    return guarded_demo

def wrap_with_login_guard_2(demo):
    with gr.Blocks() as guarded_demo:
        state = gr.State({"logged_out": False})

        # Logged out message + login button
        logged_out_view = gr.Column(visible=False)
        with logged_out_view:
            gr.Markdown("## 🚪 You are logged out.\nPlease log in to continue.")
            login_btn = gr.Button("Login")

        # App interface
        app_view = gr.Column(visible=True)
        with app_view:
            gr.Markdown(f"## ✅ You are logged in.")
            demo.render()  # Reuse the instantiated app inside the wrapper
            logout_btn = gr.Button("Logout")

        # Login/Logout logic
        def login(state_dict):
            state_dict["logged_out"] = False
            return gr.update(visible=False), gr.update(visible=True), state_dict

        def logout(state_dict):
            state_dict["logged_out"] = True
            return gr.update(visible=True), gr.update(visible=False), state_dict

        login_btn.click(login, inputs=state, outputs=[logged_out_view, app_view, state])
        logout_btn.click(logout, inputs=state, outputs=[logged_out_view, app_view, state])

    return guarded_demo

