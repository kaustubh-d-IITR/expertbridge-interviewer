
import streamlit as st
import time

def display_timer(start_time_epoch, stop=False):
    """
    Displays a robust, self-updating timer using an iframe.
    This persists across Streamlit re-runs and uses client-side JS for accuracy.
    If stop=True, it shows the final time and stops ticking.
    """
    
    # Calculate current elapsed time
    current_elapsed = int(time.time() - start_time_epoch)
    
    # HTML/JS Code
    timer_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: "Source Sans Pro", sans-serif;
                margin: 0;
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 5px;
                text-align: center;
            }}
            .timer-label {{
                font-size: 14px;
                color: #333;
                margin-bottom: 5px;
                font-weight: 600;
            }}
            .timer-display {{
                font-size: 28px;
                font-weight: bold;
                color: #000;
                font-feature-settings: "tnum";
                font-variant-numeric: tabular-nums;
            }}
            .warning {{
                color: #d93025;
                animation: pulse 2s infinite;
            }}
            .wrap-up {{
                font-size: 12px;
                color: #d93025;
                font-weight: bold;
                margin-top: 5px;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.8; }}
                100% {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <div class="timer-label">⏱️ Time Elapsed</div>
        <div id="display" class="timer-display">Loading...</div>
        <div id="msg" class="wrap-up"></div>

        <script>
            const startTime = {start_time_epoch};
            const stopTimer = {str(stop).lower()};

            function update() {{
                const now = Date.now() / 1000;
                let elapsed = Math.floor(now - startTime);
                
                if (stopTimer) {{
                     // If stopped, just show the frozen time (passed from Python via start_time calculation ideally, 
                     // but here we just accept the client time at the moment of render)
                     // Actually, if we want to freeze, we shouldn't update 'now'.
                     // But simpler: If stop is true, we just calculate once and don't set interval.
                }}

                if (elapsed < 0) {{
                    document.getElementById("display").innerText = "0m 0s";
                    return;
                }}

                const m = Math.floor(elapsed / 60);
                const s = elapsed % 60;

                const display = document.getElementById("display");
                display.innerText = `${{m}}m ${{s}}s`;

                // 13 Minute Warning
                if (elapsed >= 780 && !stopTimer) {{
                    display.classList.add("warning");
                    document.getElementById("msg").innerText = "⚠️ WRAP UP SOON";
                }}
                
                // 15 Minute Limit
                if (elapsed >= 900) {{
                    document.getElementById("msg").innerText = "🛑 TIME UP";
                }}
            }}

            update(); // Initial call
            
            if (!stopTimer) {{
                setInterval(update, 1000); // Tick every second
            }} else {{
                document.getElementById("msg").innerText = "🏁 FINISHED";
                document.getElementById("display").style.color = "#008000";
            }}
        </script>
    </body>
    </html>
    """
    
    st.components.v1.html(timer_html, height=100)
