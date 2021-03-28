import os


class UPath():
    @staticmethod
    def is_file_exists(file=''):
        return os.path.exists(file)

    @staticmethod
    def rename(src='',  dst=''):
        return os.rename(src, dst)

    @staticmethod
    def remove(file=''):
        return os.remove(file)

    @staticmethod
    def get_root_dir():
        return os.getcwd()