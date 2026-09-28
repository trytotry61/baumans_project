import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
METRICS_DIR = PROJECT_ROOT / "metrics"
def load_and_combine_data(files):
    """Считывает CSV файлы, очищает от NaN/inf и объединяет в один DataFrame."""
    dfs = []
    for f in files:
        if os.path.exists(f):
            try:
                df = pd.read_csv(f)
                # Удаляем пустые строки
                df = df.dropna(how='all')
                dfs.append(df)
            except Exception as e:
                print(f"Ошибка при чтении {f}: {e}")
        else:
            print(f"Предупреждение: Файл {f} не найден.")
    
    if not dfs:
        raise FileNotFoundError("Нет данных для анализа. Сначала запустите бенчмарки.")   
    combined = pd.concat(dfs, ignore_index=True)
    numeric_cols = ['Num_Agents', 'Exec_Time_ms', 'Peak_Memory_KB', 'Sum_of_Costs', 'Makespan']
    for col in numeric_cols:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors='coerce')
    combined = combined.replace([np.inf, -np.inf], np.nan)
    combined = combined.dropna(subset=['Num_Agents', 'Exec_Time_ms', 'Algorithm'])
    combined['Num_Agents'] = combined['Num_Agents'].astype(int)
    return combined
def print_summary_statistics(df):
    """Выводит сводную таблицу средних значений в консоль."""
    if df.empty:
        print("Нет валидных данных для отображения статистики.")
        return
    summary = df.groupby(['Algorithm', 'Num_Agents']).agg({
        'Exec_Time_ms': 'mean',
        'Peak_Memory_KB': 'mean',
        'Sum_of_Costs': 'mean',
        'Makespan': 'mean'
    }).reset_index()
    
    print("\n СВОДНАЯ СТАТИСТИКА (Средние значения) ")
    print(summary.to_string(index=False, float_format="%.2f"))

def create_dashboard(df, output_filename="benchmark_dashboard.png"):
    """Создает сетку 2x2 с графиками и сохраняет как изображение."""
    if df.empty:
        print("Ошибка: Нет валидных данных для построения графиков.")
        return
    sns.set_theme(style="whitegrid", palette="Set1")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Сравнение алгоритмов маршрутизации', fontsize=20, fontweight='bold', y=0.95)
    sns.lineplot(data=df, x='Num_Agents', y='Exec_Time_ms', hue='Algorithm', 
                 marker='o', ax=axes[0, 0], err_style='band')
    axes[0, 0].set_title('Время выполнения (мс)', fontsize=14)
    axes[0, 0].set_ylabel('Время (ms)')
    axes[0, 0].set_xlabel('Количество агентов')
    axes[0, 0].set_yscale('log')
    sns.lineplot(data=df, x='Num_Agents', y='Peak_Memory_KB', hue='Algorithm', 
                 marker='o', ax=axes[0, 1], err_style='band')
    axes[0, 1].set_title('Пиковое потребление памяти (КБ)', fontsize=14)
    axes[0, 1].set_ylabel('Память (KB)')
    axes[0, 1].set_xlabel('Количество агентов')
    sns.lineplot(data=df, x='Num_Agents', y='Sum_of_Costs', hue='Algorithm', 
                 marker='o', ax=axes[1, 0], err_style='band')
    axes[1, 0].set_title('Суммарная длина путей (Sum of Costs)', fontsize=14)
    axes[1, 0].set_ylabel('Шаги')
    axes[1, 0].set_xlabel('Количество агентов')
    sns.lineplot(data=df, x='Num_Agents', y='Makespan', hue='Algorithm', 
                 marker='o', ax=axes[1, 1], err_style='band')
    axes[1, 1].set_title('Время завершения миссии (Makespan)', fontsize=14)
    axes[1, 1].set_ylabel('Шаги')
    axes[1, 1].set_xlabel('Количество агентов')
    max_agents = int(df['Num_Agents'].max())
    for ax in axes.flat:
        ax.set_xticks(range(1, max_agents + 1))
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles=handles, labels=labels, loc='upper left')
    plt.tight_layout(rect=[0, 0.03, 1, 0.93])
    plt.savefig(output_filename, dpi=300)
    print(f"Дашборд успешно сохранен в файл: {output_filename}")
    plt.show()

if __name__ == "__main__":
    csv_files = [
        METRICS_DIR / "metrics_cbs.csv",
        METRICS_DIR / "metrics_dstar.csv",
        METRICS_DIR / "metrics_hybride.csv"
    ]
    
    dashboard_output = METRICS_DIR / "benchmark_dashboard.png"
    
    try:
        data = load_and_combine_data(csv_files)
        print_summary_statistics(data)
        create_dashboard(data, output_filename=dashboard_output)
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")