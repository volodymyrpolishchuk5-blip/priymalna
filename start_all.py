import subprocess
import threading
import time
import os
import sys

def run_server():
    print("Запуск веб-сервера...")
    subprocess.run([sys.executable, "server.py"])

def run_bot():
    print("Запуск бота...")
    subprocess.run([sys.executable, "bot.py"])

if __name__ == "__main__":
    # Запускаємо сервер у фоновому потоці
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(2) # Даємо серверу час запуститися

    print("\n" + "="*50)
    print("СЕРВЕР ПРАЦЮЄ НА ПОРТУ 8000")
    print("Тепер вам потрібно запустити тунель.")
    print("Виконайте цю команду в ОКРЕМОМУ терміналі:")
    print("\nssh -R 80:localhost:8000 nokey@localhost.run")
    print("\nПісля запуску ви отримаєте URL (наприклад, https://abc123.lhr.life).")
    print("Скопіюйте його, додайте '/index.html' в кінець і вставте в .env файл.")
    print("="*50 + "\n")

    # Запускаємо бота (це заблокує основний потік)
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Робота завершена.")
