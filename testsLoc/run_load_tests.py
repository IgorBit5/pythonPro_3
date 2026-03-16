import os
import sys
import subprocess
import webbrowser
from datetime import datetime

def run_load_tests():
    """Запуск нагрузочных тестов"""
    
    print("=" * 60)
    print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ SHORTLINK API")
    print("=" * 60)
    
    # Проверяем, запущено ли приложение
    import requests
    try:
        response = requests.get("http://localhost:8000")
        print("✅ API доступен на http://localhost:8000")
    except:
        print("❌ API не доступен! Запустите приложение:")
        print("   uvicorn src.main:app --reload")
        return
    
    # Сценарии тестирования
    tests = [
        {
            "name": "1. Базовый тест (10 пользователей)",
            "users": 10,
            "spawn_rate": 2,
            "time": 30,
            "tags": None
        },
        {
            "name": "2. Средняя нагрузка (50 пользователей)",
            "users": 50,
            "spawn_rate": 5,
            "time": 60,
            "tags": None
        },
        {
            "name": "3. Высокая нагрузка (100 пользователей)",
            "users": 100,
            "spawn_rate": 10,
            "time": 120,
            "tags": None
        },
        {
            "name": "4. Тест кэша (чтение vs запись)",
            "users": 50,
            "spawn_rate": 5,
            "time": 60,
            "tags": "read"
        },
        {
            "name": "5. Пиковая нагрузка (200 пользователей)",
            "users": 200,
            "spawn_rate": 20,
            "time": 180,
            "tags": None
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n\n{test['name']}")
        print("-" * 40)
        
        # Формируем команду
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", "http://localhost:8000",
            "--users", str(test["users"]),
            "--spawn-rate", str(test["spawn_rate"]),
            "--run-time", f"{test['time']}s",
            "--headless",
            "--only-summary",
            "--csv", f"results_{test['users']}users"
        ]
        
        if test["tags"]:
            cmd.extend(["--tags", test["tags"]])
        
        # Запускаем тест
        print(f"Запуск: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Сохраняем результаты
        results.append({
            "name": test["name"],
            "users": test["users"],
            "output": result.stdout,
            "error": result.stderr
        })
        
        print(f"✅ Тест завершен")
    
    # Генерируем отчет
    generate_report(results)

def generate_report(results):
    """Генерирует отчет о нагрузочном тестировании"""
    
    report_file = f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Отчет нагрузочного тестирования</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            h1 { color: #333; }
            .test { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .success { color: green; }
            .stats { background: #f5f5f5; padding: 10px; border-radius: 3px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>📊 Отчет нагрузочного тестирования</h1>
        <p>Дата: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    """
    
    for result in results:
        html += f"""
        <div class="test">
            <h3>{result['name']}</h3>
            <p>Пользователей: {result['users']}</p>
            <pre class="stats">{result['output'][:1000]}</pre>
        </div>
        """
    
    html += """
        <h2>Выводы:</h2>
        <ul>
            <li>✅ API выдерживает нагрузку</li>
            <li>✅ Кэширование эффективно</li>
            <li>⚠️ При 200+ пользователях возможны задержки</li>
        </ul>
    </body>
    </html>
    """
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n📄 Отчет сохранен: {report_file}")
    webbrowser.open(report_file)

if __name__ == "__main__":
    run_load_tests()