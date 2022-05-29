import multiprocessing
from dm_storager.cli import entry_point as main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
