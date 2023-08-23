# coding=utf-8
import os
import time
import platform
import tkinter
from tkinter import *
from HCNetSDK import *

# 系统环境标识
WINDOWS_FLAG = True

# 报警信息列表，报一次在回调中加1次记录
alarm_info = []

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
        sdk.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        sdk.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
        sdk.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
    else:
        strPath = os.getcwd().encode('utf-8')
        sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
        sdk_ComPath.sPath = strPath
        sdk.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        sdk.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
        sdk.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))

# 报警信息回调函数实现代码
def g_fMessageCallBack_Alarm(lCommand, pAlarmer, pAlarmInfo, dwBufLen, pUser):
    # 解析报警信息
    global alarm_info
    Alarmer = pAlarmer.contents  # 取指针指向的结构体
    single_alrm = {}
    deviceSeriel = ''
    deviceIP = ''
    single_alrm['lCommand'] = hex(lCommand)

    if Alarmer.bySerialValid:
        for n in Alarmer.sSerialNumber[0:48]:
            if n != 0:
                deviceSeriel += chr(n)
        single_alrm['设备序列号:'] = deviceSeriel

    if Alarmer.byDeviceIPValid:
        for n in Alarmer.sDeviceIP[0:128]:
            if n != 0:
                deviceIP += chr(n)
        single_alrm['设备IP: '] = deviceIP

    if Alarmer.byUserIDValid:
        single_alrm['lUserID'] = Alarmer.lUserID

    # 移动侦测、视频丢失、遮挡、IO信号量等报警信息(V3.0以上版本支持的设备)
    if lCommand == 0x4000:
        print('移动侦测')
        Alarm_struct = cast(pAlarmInfo, LPNET_DVR_ALARMINFO_V30).contents
        # 当lCommand是COMM_ALARM时将pAlarmInfo强制转换为NET_DVR_ALARMINFO类型的指针再取值
        single_alrm['dwAlarmType'] = hex(Alarm_struct.dwAlarmType)
        single_alrm['byAlarmOutputNumber'] = Alarm_struct.byAlarmOutputNumber[0]
        single_alrm['byChannel'] = Alarm_struct.byChannel[0]

    # 门禁报警事件上传
    if lCommand == 0x5002:
        print('门禁触发报警')
        Alarm_struct = cast(pAlarmInfo, LPNET_DVR_ACS_ALARM_INFO).contents
        # 当lCommand是0x5002时将pAlarmInfo强制转换为NET_DVR_ACS_ALARM_INFO类型的指针再取值
        single_alrm['dwMajor'] = hex(Alarm_struct.dwMajor)
        single_alrm['dwMinor'] = hex(Alarm_struct.dwMinor)
        single_alrm['dwPicDataLen'] = Alarm_struct.dwPicDataLen
        localtime = time.asctime(time.localtime(time.time()))
        single_alrm['localtime'] = localtime
        # 抓拍图片
        PicDataLen = Alarm_struct.dwPicDataLen
        if PicDataLen != 0:
            buff1 = string_at(Alarm_struct.pPicData, PicDataLen)
            with open('../../pic/Acs_Capturetest.jpg', 'wb') as fp:
                fp.write(buff1)

    # 身份证刷卡事件上传
    if lCommand == 0x5200:
        print('身份证刷卡事件上传')
        Alarm_struct = cast(pAlarmInfo, LPNET_DVR_ID_CARD_INFO_ALARM).contents
        single_alrm['dwMajor'] = hex(Alarm_struct.dwMajor)
        single_alrm['dwMinor'] = hex(Alarm_struct.dwMinor)
        localtime = time.asctime(time.localtime(time.time()))
        single_alrm['localtime'] = localtime
        #抓拍图片
        DataLen = Alarm_struct.dwCapturePicDataLen
        if DataLen != 0:
            buff1 = string_at(Alarm_struct.pCapturePicData, DataLen)
            with open('../../pic/IDInfo_Capturetest.jpg', 'wb') as fp1:
                fp1.write(buff1)
        #身份证图片
        CardPicLen = Alarm_struct.dwPicDataLen
        if DataLen != 0:
            buff2 = string_at(Alarm_struct.pPicData, CardPicLen)
            with open('../../pic/IDInfo_IDPicTest.jpg', 'wb') as fp2:
                fp2.write(buff2)

    # ISAPI协议报警信息
    if lCommand == 0x6009:
        print('ISAPI协议报警信息上传')
        Alarm_struct = cast(pAlarmInfo, LPNET_DVR_ALARM_ISAPI_INFO).contents
        single_alrm['byDataType'] = Alarm_struct.byDataType
        single_alrm['byPicturesNumber'] = Alarm_struct.byPicturesNumber

        # 报警信息XML或者JSON数据
        DataLen = Alarm_struct.dwAlarmDataLen
        if DataLen != 0:
            buffInfo = string_at(Alarm_struct.pAlarmData, DataLen)
            with open('../../pic/IsapiInfo.txt', 'wb') as fpInfo:
                fpInfo.write(buffInfo)

        # 报警信息图片数据
        nSize = 0
        pNum = Alarm_struct.byPicturesNumber
        if pNum > 0:
            STRUCT = NET_DVR_ALARM_ISAPI_PICDATA * pNum
            PicStruct = cast(Alarm_struct.pPicPackData, POINTER(STRUCT)).contents
            for nPicIndex in range(pNum):
                nSize = PicStruct[nPicIndex].dwPicLen
                print(nSize)
                if nSize != 0:
                    buffInfo = string_at(PicStruct[nPicIndex].pPicData, nSize)
                    strPicName = ''
                    for n in PicStruct[nPicIndex].szFilename[0:256]:
                        if n != 0:
                            strPicName += chr(n)
                    single_alrm['PicName'] = strPicName
                    sFileName = ('../../pic/ISAPI_Pic[%d].jpg' % nPicIndex)
                    with open(sFileName, 'wb') as fpPic:
                        fpPic.write(buffInfo)

    alarm_info.append(single_alrm)
    # print(alarm_info[-1])
    tt.insert(tkinter.END, alarm_info[-1])
    tt.insert(tkinter.END, '\r\n---------------\r\n')
    return

# 回调函数定义，需要是全局的
setdvrmsg_callback_func = MSGCallBack(g_fMessageCallBack_Alarm)

if __name__ == '__main__':
    # 创建窗口, 用于显示接收到的事件数据
    win = tkinter.Tk()
    # 固定窗口大小
    win.resizable(0, 0)
    win.overrideredirect(True)

    sw = win.winfo_screenwidth()
    # 得到屏幕宽度
    sh = win.winfo_screenheight()
    # 得到屏幕高度

    # 窗口宽高
    ww = 512
    wh = 384
    x = (sw - ww) / 2
    y = (sh - wh) / 2
    win.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

    # 创建退出按键
    b = Button(win, text='退出', command=win.quit)
    b.pack()
    # 创建显示报警信息的文本框
    tt = tkinter.Text(win, width=ww, height=wh, bg='white')
    tt.pack()

    # 获取系统平台
    GetPlatform()

    # 加载库,先加载依赖库
    if WINDOWS_FLAG:
        os.chdir(r'./lib/win')
        sdk = ctypes.CDLL(r'./HCNetSDK.dll')
    else:
        os.chdir(r'./lib/linux')
        sdk = cdll.LoadLibrary(r'./libhcnetsdk.so')

    SetSDKInitCfg()  # 设置组件库和SSL库加载路径

    # 初始化
    sdk.NET_DVR_Init()
    # 启用SDK写日志
    sdk.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding='utf-8'), False)

    # 通用参数配置
    sdkCfg = NET_DVR_LOCAL_GENERAL_CFG()
    sdkCfg.byAlarmJsonPictureSeparate = 1
    sdk.NET_DVR_SetSDKLocalCfg(17, byref(sdkCfg))

    # 启动报警监听并且设置回调函数接收事件
    handle = sdk.NET_DVR_StartListen_V30(bytes('10.17.35.47', 'ascii'), 7200, setdvrmsg_callback_func, None)
    if handle < 0:
        print("NET_DVR_StartListen_V30失败, error code: %d" % sdk.NET_DVR_GetLastError())
        sdk.NET_DVR_Cleanup()
        exit()

    # show Windows
    win.mainloop()
    # 等待接收报警信息，如果需要一直接收事件，程序进程需要一直运行，不要退出

    # 停止监听
    sdk.NET_DVR_StopListen_V30(handle)
    # 释放SDK资源，退出程序时调用
    sdk.NET_DVR_Cleanup()
