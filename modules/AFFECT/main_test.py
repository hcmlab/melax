import affect_modules
import time

if __name__ == '__main__':
    affect_worker = affect_modules.AffectWorker()
    affect_worker.bind()
    affect_worker.start()

    time.sleep(10)

    affect_worker.stop()
