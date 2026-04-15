import pyautogui
import time

print("=== 滑鼠座標顯示器 ===")
print("把滑鼠移到你想要的位置（例如 AI 的輸入框），按 Ctrl + C 停止")
print("座標會每 0.5 秒更新一次\n")

try:
    while True:
        x, y = pyautogui.position()
        print(f"X: {x:4d}   Y: {y:4d}", end="\r")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n\n已停止。最後位置是 X:", x, "Y:", y)