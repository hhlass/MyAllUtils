import os
import shutil
import logging

__chunkSize = 1024 * 1024 * 50  # 分块大小 50MB
__splitMinSize = int(__chunkSize * 1.2)  # 需要分割的最小文件大小
__splitRootPath = "./split/"       #切割后文件存放根目录
__mergeRootPath = "./merge/"    #合并后文件存放根目录
#一下参数针对切割
__allNums = 0       #处理文件总数
__splitNums = 0     #切割文件个数
__copyNums = 0      #复制文件个数


# 读取文件
def __getFile(filePath):
    if not os.path.exists(filePath):    #判断源文件是否存在
        logging.error("目标文件不存在!")
        exit(-1)
    try:
        f = open(filePath, 'rb')
        return f
    except:
        logging.error("无法读取文件!")
    return None


# 判断是否需要切割
def __isNeedSplit(filePath):
    return os.path.getsize(filePath) > __splitMinSize


# 写入切割块
def __saveChunk(chunk, targetFilePath):
    try:
        with open(targetFilePath, 'wb') as f:
            f.write(chunk)
        return True
    except Exception as e:
        logging.error("{} 写入失败!".format(targetFilePath))
        logging.error(e)
    return False


# 切割存储目标文件路径
def __getTargetFilePath(filePath):
    file = os.path.split(filePath)[1]
    if not os.path.exists(__splitRootPath + file):  #判断切割存储当前文件的目录是否存在,不存在则创建
        os.makedirs(__splitRootPath + file)
    return __splitRootPath + file


# 切割单个文件
def __splitSingle(filePath):
    targetFilePath = __getTargetFilePath(filePath)
    if not __isNeedSplit(filePath): #判断文件是否需要切割,无需切割则复制文件到目标位置并重命名
        logging.error("{} 无需切割,直接复制到目标地址 {}".format(filePath, targetFilePath))
        try:
            global __copyNums
            shutil.copyfile(filePath, targetFilePath + "/1.hhlass")
            __copyNums += 1
            logging.info("复制成功")
        except:
            logging.error("复制失败!")
        return
    f = __getFile(filePath)
    if f is None:
        logging.error("文件读取失败!")
        return
    try:
        global __splitNums
        index = 1
        while True:
            chunk = f.read(__chunkSize)
            if not chunk:
                logging.info("{} 文件分割结束!".format(filePath))
                break
            flag = __saveChunk(chunk, "{}/{}.hhlass".format(targetFilePath, str(index)))
            if flag:
                logging.info("{} 文件第{}部分分割成功!".format(filePath, str(index)))
                index += 1
            else:
                logging.error("{} 文件第{}部分分割失败!".format(filePath, str(index)))
                logging.info("跳过当前文件 {}".format(filePath))
                break
        __splitNums += 1
    except Exception as e:
        print(e)
    finally:
        f.close()


# 批量切割文件
def splitFiles(paths):
    global __allNums
    if not os.path.exists(paths):
        logging.error("输入路径不存在!")
        exit(-1)
    if os.path.isfile(paths):
        __splitSingle(paths)
        __allNums += 1
        return
    for path in os.listdir(paths):
        splitFiles(paths + "/" + path)
    logging.info("{} 切割完成!".format(paths))


# 获取需要合并的文件夹的文件数
def __getFileNums(filePath):
    if not os.path.exists(filePath):
        return -1
    fileNums = 0
    for file in os.listdir(filePath):
        if os.path.isdir(filePath + "/" + file):
            return -1
        fileNums += 1
    return fileNums


# 合并单个文件
def mergeSingle(filePath):
    fileNums = __getFileNums(filePath)
    if fileNums == -1:
        logging.info("{} 文件夹中存在文件夹!")
    elif fileNums == 0:
        logging.info("{} 为空文件夹")
    else:
        if not os.path.exists(__mergeRootPath):
            os.makedirs(__mergeRootPath)
        file = __mergeRootPath + os.path.split(filePath)[1]
        if fileNums == 1:
            try:
                shutil.copyfile("{}/{}.hhlass".format(filePath, str(fileNums)), file)
            except Exception as e:
                logging.error("{} 合并失败!".format(file))
                return
            logging.info("{} 合并成功!".format(file))
        else:
            write = open(file, 'wb')
            try:
                for i in range(1, fileNums + 1):
                    with open("{}/{}.hhlass".format(filePath, str(i)), 'br') as read:
                        write.write(read.read())
            except Exception as e:
                logging.error("{} 合并失败!".format(filePath))
                logging.error(e)
                return
            finally:
                write.close()
        logging.info("{} 合并完成!".format(file))


## 分割函数 splitFiles("<文件夹或是文件>") 可以传入文件夹,会递归切割所有文件
## 合并函数 mergeSingle("文件夹")  传入文件夹路径内不能包含文件夹
## 合并函数仅能用于由分割函数分割出来的文件合并
if __name__ == '__main__':
    # splitFiles("<path>")
    # print("总共处理文件数:{}, 切割文件数:{}, 复制文件数:{}".format(str(__allNums),str(__splitNums),str(__copyNums)))
    # mergeSingle("<path>")
    pass
