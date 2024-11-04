from toil.utils.toilStatus import ToilStatus

# Укажите путь к jobStore
job_store_path = "/mnt/c/Users/vtatt/my-jobstore-20"

# Создайте объект ToilStatus
status = ToilStatus(job_store_path)

# Генерация графика в формате DOT
status.print_dot_chart()
