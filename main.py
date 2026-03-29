import time
import random
import matplotlib.pyplot as plt

# Пузырьковая сортировка (O(n²))
def bubble_sort(arr):
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

# Замер времени выполнения
def measure_time(sort_func, arr):
    start = time.perf_counter()
    sort_func(arr)
    return time.perf_counter() - start

# Размеры массивов
n_values = [1000, 2000, 5000, 10000]

# Списки для хранения средних времён
bubble_times = []
sorted_times = []

print("Выполнение замеров...")
print("-" * 50)

# Проводим замеры для каждого n
for n in n_values:
    bubble_total = 0
    sorted_total = 0
    
    repeats = 3
    for _ in range(repeats):
        arr_original = [random.randint(0, 100000) for _ in range(n)]
        
        arr1 = arr_original.copy()
        bubble_total += measure_time(bubble_sort, arr1)
        
        arr2 = arr_original.copy()
        sorted_total += measure_time(sorted, arr2)
    
    bubble_avg = bubble_total / repeats
    sorted_avg = sorted_total / repeats
    
    bubble_times.append(bubble_avg)
    sorted_times.append(sorted_avg)
    
    print(f"n = {n:5d} | Пузырьковая: {bubble_avg:.6f} сек | sorted(): {sorted_avg:.6f} сек")

print("-" * 50)

# Построение графика
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# График 1: O(n^2)
axes[0].plot(
    n_values,
    bubble_times,
    'o-',
    color='red',
    linewidth=2,
    markersize=8,
    label='bubble_sort: O(n^2)'
)
axes[0, 0].set_xlabel('Размер массива n')
axes[0, 0].set_ylabel('Время выполнения (сек)')
axes[0, 0].set_title('O(n^2): bubble_sort (time)')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

axes[1, 0].plot(
    n_values,
    [bubble_times[i] / n2_values[i] for i in range(len(n_values))],
    'o-',
    color='red',
    linewidth=2,
    markersize=8,
    label='bubble_time / n^2'
)
axes[1, 0].set_xlabel('Размер массива n')
axes[1, 0].set_ylabel('Нормированное время')
axes[1, 0].set_title('O(n^2): bubble_sort (time / n^2)')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

# График 2: O(n log n)
axes[1].plot(
    n_values,
    sorted_times,
    'o-',
    color='blue',
    linewidth=2,
    markersize=8,
    label='sorted(): O(n log n)'
)
axes[1].set_xlabel('Размер массива n')
axes[1].set_ylabel('Время выполнения (сек)')
axes[1].set_title('Встроенная sorted() (O(n log n))')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.show()