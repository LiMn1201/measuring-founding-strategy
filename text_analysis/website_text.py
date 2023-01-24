import os
from bs4 import BeautifulSoup
import sys
import pdb
import os
import re
import mimetypes
sys.path.append(os.path.abspath('../crawler'))
from waybackmachine_crawler import waybackmachine_crawler
sys.path.append(os.path.abspath('../download'))
from data_reader import data_reader


class website_text:

    def __init__(self, path, domain, year, incyear = None, skip_memory_error = False):
        mimetypes.init()
        domain = data_reader.clean_domain_url(domain)
        self.texts = self.load_domain(path, domain, year, incyear , skip_memory_error = skip_memory_error) 
        #为什么texts在下面没有定义过？ load_domain在下面做了定义
        

    #在字符之间插入空格
    def get_website_text(self):
        if self.texts is not None:
            return " ".join(self.texts)
        else:
            return ""

    #清洗文本，去掉特殊标点符号    
    def clean_page_text(self, text, skip_memory_error = False):
        #initial_text = text
        try:
            text= re.sub(r"[\s,:#][\.\-@]?[\d\w]+[\.\-@][\d\w\.\-@_]*"," ",text)
            text= re.sub(r"[\s,:][\.\-@][\d\w]+"," ",text)
            text= re.sub(r"\s\d[\d\w]+"," ",text)
            text= re.sub(r"[{}>\*/\';]"," ",text)
            text= re.sub(r"\s+"," ",text)
            text= re.sub(r"DOMContentLoaded.*_static"," ",text)

            #remove all these random unicode words
            #text = re.sub(r"(\W|^)\w*" + '\x00' + "\w*\W"," ",text)
            #text = re.sub(r"(\W|^)\w*" + '\x01' + "\w*\W"," ",text)
            #text= re.sub(r"(\W|^)\w*" + '\x03' + "\w*\W"," ",text)
            return text
        except MemoryError as e:
            if skip_memory_error:
                print("\t --> Memory Error in method clean_page_text.. Skipping")
                return ""
            else:
                raise e

    #清除pdf文档
    def is_html_page(self,text):
        #remove downloaded PDFs, this is rarely used, since most are deleted when the
        #algorithm filters through bad_mimes. #所以应该在load_page后面
        if text[0:3]=="PDF" or text[1:4] == "PDF":
            return False

        if text[0:3] == "PNG" or text[1:4] == "PNG":
            return False

        #any page this long has something wrong for sure.  100K characters are 120 letter pages!
        if len(text) > 100000:
            return False
        
        return True


    #计算长度后剔除小于50或等于1706的文本
    def is_valid_website(self):
        text_len = len(self.get_website_text())

        #this is only the WAybackMachine data
        if text_len == 1706 or text_len < 50:  
            return False

        else:
            return True

    #对于爬取的文本进行格式的处理和清洗    
    def load_page(self, page_file_path, skip_memory_error = False, char_limit=1000000):
        try:
            bad_mimes = ['application/pdf','text/x-perl','image/jpeg','application/x-msdos-program',
                         'image/gif', 'text/vcard','application/msword','application/xml',
                         'video/x-ms-wmv', 'text/css','text/vnd.sun.j2me.app-descriptor']            
            
            (mime, x) = mimetypes.guess_type(page_file_path) #为什么这个就简化后面用了mime呢？
            #把其他类型的数据剔除掉
            if mime is not None:
                #remove all undesired types of data that is not text to include into NLP
                if mime in bad_mimes:
                    return ""
                if mime.split("/")[0] in ['application','video','image','audio']:
                    return ""
            
            if mime not in ['text/html','text/plain'] and mime is not None:
                #pdb.set_trace()
                pass
            #爬取文本
            f = open(page_file_path)
            html = f.read()
            soup = BeautifulSoup(html,"html.parser")
            text = soup.get_text(separator = ' ')

            #just a limit of 1 million characters to avoid memory errors
            text = text[0:char_limit]
            
            return self.clean_page_text(text)
        except (TypeError, UnboundLocalError):
            print("\t. --> There was one error, skipping this page")
            return ""
        except MemoryError as e:
            if skip_memory_error:
                print("\t --> Memory Error.. Skipping")
                return ""
            else:
                raise e
    #生成路径名
    def load_domain(self, path, domain, year=None, incyear = None, force_download=False,skip_memory_error = False):
        clean_domain = data_reader.clean_domain_url(domain)
        root_folder = "{0}/{1}".format(path,clean_domain).replace("//","/")

        if year is None:
            file_folder = root_folder
        else: 
            file_folder = "{0}/{1}/{2}".format(path,clean_domain, year).replace("//","/")#路径名加上year

        
        
        if  os.path.exists(root_folder) is False or os.path.exists(file_folder) is False or os.path.isdir(file_folder) is False: #如果路径是不正确的
            if force_download is True: #force_download在下面做了定义
                #depends on whether it is startup download of public download
                pdb.set_trace() #程序运行到这里暂停
                download_year = year if year is not None else incyear #对download_year进行赋值
                download_year = int(download_year)
                self.force_download(root_folder , domain, download_year)
            else:
                return None
            
        files = []
        for file_name in os.listdir(file_folder): #用listdir获取file_folder下所有文件的路径
            text = self.load_page(file_folder + "/" + file_name, skip_memory_error = skip_memory_error)
            if self.is_html_page(text): #如果text不是pdf文件的话
                text = re.sub(r"\s+"," ",text) r"\s+" #对应的内容替换成空格
                files.append(text)

        return files



    
    def force_download(self,path, domain, year):
        year_folder = year is not None #year非空

        crawler = waybackmachine_crawler(website = domain, output_folder = path , year_folder = year_folder)
        crawler.crawl_from_date(year, 12, 31)
