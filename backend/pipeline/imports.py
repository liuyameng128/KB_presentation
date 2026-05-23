import os
os.environ["CUDA_VISIBLE_DEVICES"] = "4" 

import sys 
import time
from pathlib import Path
from paddleocr import PPStructureV3
import paddle
import gc

# 章节文件 批量 预处理和分块
import time
import re
import pandas as pd
from tqdm import tqdm
import requests
import json 
from typing import Optional   
import tiktoken # 确保已安装: pip install tiktoken
from bs4 import BeautifulSoup  
 
from pydantic import BaseModel
from typing import List
from ollama import chat  
    
from typing import Union

import json
# import torch
import numpy as np
import requests
import pandas as pd
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
