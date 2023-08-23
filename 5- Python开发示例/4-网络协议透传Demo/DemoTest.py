# coding=utf-8

import ctypes
import os
import platform
import time
import tkinter
import json
from ctypes import *
from HCNetSDK import *

# 系统环境标识
WINDOWS_FLAG = True

# 获取当前系统环境
def GetPlatform():
    sysstr = platform.system()
    print('' + sysstr)
    if sysstr != "Windows":
        global WINDOWS_FLAG
        WINDOWS_FLAG = False

# 设置SDK初始化依赖库路径
def SetSDKInitCfg():
    # 设置HCNetSDKCom组件库和SSL库加载路径
    # print(os.getcwd())  
    if WINDOWS_FLAG:
        strPath = os.getcwd().encode('gbk')
        sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
        sdk_ComPath.sPath = strPath
        sdkTest.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        sdkTest.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
        sdkTest.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
    else:
        strPath = os.getcwd().encode('utf-8')
        sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
        sdk_ComPath.sPath = strPath
        sdkTest.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        sdkTest.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
        sdkTest.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))
        
def LoginDev():
    # 设备登录信息
    struLoginInfo = NET_DVR_USER_LOGIN_INFO()
    struLoginInfo.bUseAsynLogin = 0  # 同步登录方式
    struLoginInfo.sDeviceAddress = bytes("10.17.35.231", "ascii")  # 设备IP地址
    struLoginInfo.wPort = 8000  # 设备服务端口
    struLoginInfo.sUserName = bytes("admin", "ascii")  # 设备登录用户名
    struLoginInfo.sPassword = bytes("abcd1234", "ascii")  # 设备登录密码

    # 设备信息, 输出参数
    struDeviceInfoV40 = NET_DVR_DEVICEINFO_V40()

    #登录设备
    iUserID = sdkTest.NET_DVR_Login_V40(byref(struLoginInfo), byref(struDeviceInfoV40))
    if iUserID < 0:
        print('登录失败, 错误码: %d' % sdkTest.NET_DVR_GetLastError())
    else:
        print('登录成功，设备序列号：%s' % str(struDeviceInfoV40.struDeviceV30.sSerialNumber, encoding="utf8"))
    return iUserID

def Close(lUserID):
    if lUserID >= 0:
        # 注销用户
        sdkTest.NET_DVR_Logout(lUserID)
        # 释放SDK资源
        sdkTest.NET_DVE_Cleanup()

def getShowString(lUserID):
    xmlInput = NET_DVR_XML_CONFIG_INPUT()
    xmlInput.dwSize = sizeof(xmlInput)
    url = create_string_buffer(b'GET /ISAPI/System/Video/inputs/channels/1/overlays/text/1')
    xmlInput.lpRequestUrl = addressof(url)
    # print(xmlInput.lpRequestUrl)
    xmlInput.dwRequestUrlLen = len(url)
    # print(len(url))
    xmlInput.lpInBuffer = None  # 获取参数时输入为空
    xmlInput.dwInBufferSize = 0
    xmlInput.dwRecvTimeOut = 5000  # 超时时间
    xmlInput.byForceEncrpt = 0

    xmlOutput = NET_DVR_XML_CONFIG_OUTPUT()  # 输出参数
    xmlOutput.dwSize = sizeof(xmlOutput)
    xmlOutput.dwOutBufferSize = 8 * 1024
    xmlOutput.dwStatusSize = 1024
    M1 = 8 * 1024
    buff1 = (c_ubyte * M1)()
    M2 = 1024
    buff2 = (c_ubyte * M2)()

    xmlOutput.lpOutBuffer = addressof(buff1)
    xmlOutput.lpStatusBuffer = addressof(buff2)

    if sdkTest.NET_DVR_STDXMLConfig(lUserID, byref(xmlInput), byref(xmlOutput)) == 1:
        print('---获取成功---')
        # 获取成功，输出结果
        Bbytes_Out = string_at(xmlOutput.lpOutBuffer, xmlOutput.dwOutBufferSize)
        strOutput = str(Bbytes_Out, 'UTF-8')
        print(strOutput + '\n')
        # 状态信息
        '''Bbytes_Status = string_at(xmlOutput.lpStatusBuffer, xmlOutput.dwStatusSize)
        strStatus = str(Bbytes_Status)
        print(strStatus + '\n')'''
    else:
        # 接口返回失败，错误号错误号判断原因
        print('NET_DVR_STDXMLConfig接口调用失败，错误码：%d，登录句柄：%d' % (sdkTest.NET_DVR_GetLastError(), lUserID))


def setShowString(lUserID):
    xmlInput = NET_DVR_XML_CONFIG_INPUT()

    xmlInput.dwSize = sizeof(xmlInput)
    url = create_string_buffer(b'PUT /ISAPI/System/Video/inputs/channels/1/overlays/text/1')

    xmlInput.lpRequestUrl = addressof(url)
    xmlInput.dwRequestUrlLen = len(url)
    # 输入参数
    str_bytes = bytes('<TextOverlay xmlns=\"http://www.hikvision.com/ver20/XMLSchema\" version=\"2.0\">'
                          '<id>1</id>'
                          '<enabled>true</enabled>'
                          '<positionX>100</positionX>'
                          '<positionY>200</positionY>'
                          '<displayText>1234567测试abc</displayText></TextOverlay>', encoding="utf-8")

    iLen = len(str_bytes)
    xmlInput.lpInBuffer = cast(str_bytes, c_void_p)
    xmlInput.dwInBufferSize = iLen
    xmlInput.dwRecvTimeOut = 5000
    xmlInput.byForceEncrpt = 0

    xmlOutput = NET_DVR_XML_CONFIG_OUTPUT()
    xmlOutput.dwSize = sizeof(xmlOutput)
    xmlOutput.dwOutBufferSize = 8 * 1024
    xmlOutput.dwStatusSize = 1024
    M1 = 8 * 1024
    buff1 = (c_ubyte * M1)()
    M2 = 1024
    buff2 = (c_ubyte * M2)()

    xmlOutput.lpOutBuffer = addressof(buff1)
    xmlOutput.lpStatusBuffer = addressof(buff2)

    reValue = sdkTest.NET_DVR_STDXMLConfig(lUserID, byref(xmlInput), byref(xmlOutput))
    if reValue == 1:
        print('---设置成功---')
        # 设置成功，输出结果
        '''Bbytes_Out = string_at(xmlOutput.lpOutBuffer, xmlOutput.dwOutBufferSize)
        strOutput = str(Bbytes_Out)
        print(strOutput + '\n')'''
        # 状态信息
        Bbytes_Status = string_at(xmlOutput.lpStatusBuffer, xmlOutput.dwStatusSize)
        strStatus = str(Bbytes_Status, 'UTF-8')
        print(strStatus + '\n')
    else:
        # 接口返回失败，错误号错误号判断原因
        print('NET_DVR_STDXMLConfig接口调用失败，错误码：%d，登录句柄：%d' % (sdkTest.NET_DVR_GetLastError(), lUserID))


if __name__ == '__main__':
    # 获取系统平台
    GetPlatform()

    # 加载库,先加载依赖库
    if WINDOWS_FLAG:
        os.chdir(r'./lib/win')
        sdkTest = ctypes.CDLL(r'./HCNetSDK.dll')
    else:
        os.chdir(r'./lib/linux')
        sdkTest = cdll.LoadLibrary(r'./libhcnetsdk.so')

    SetSDKInitCfg()  # 设置组件库和SSL库加载路径

    # 初始化
    sdkTest.NET_DVR_Init()
    # 启用SDK写日志
    sdkTest.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)

    # 注册登录设备
    iUserID = LoginDev()
    if iUserID < 0:
        print('登录失败，退出')
    else:
        setShowString(iUserID)  # 透传方式设置通道字符叠加参数
        getShowString(iUserID)  # 透传方式获取通道字符叠加参数
