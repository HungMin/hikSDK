# coding=utf-8
import os
import platform
import time
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
    """
    解析报警信息
    """
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
        Alarm_struct = cast(pAlarmInfo,
                            LPNET_DVR_ALARMINFO_V30).contents  # 当lCommand是COMM_ALARM时将pAlarmInfo强制转换为NET_DVR_ALARMINFO类型的指针再取值
        single_alrm['dwAlarmType'] = hex(Alarm_struct.dwAlarmType)
        single_alrm['byAlarmOutputNumber'] = Alarm_struct.byAlarmOutputNumber[0]
        single_alrm['byChannel'] = Alarm_struct.byChannel[0]

    if lCommand == 0x5002:
        print('门禁触发报警')
        Alarm_struct = cast(pAlarmInfo,
                            LPNET_DVR_ACS_ALARM_INFO).contents  # 当lCommand是0x5002时将pAlarmInfo强制转换为NET_DVR_ACS_ALARM_INFO类型的指针再取值
        single_alrm['dwSize'] = Alarm_struct.dwSize
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

    if lCommand == 0x5200:
        print('身份证刷卡事件上传')
        Alarm_struct = cast(pAlarmInfo,LPNET_DVR_ID_CARD_INFO_ALARM).contents
        single_alrm['dwSize'] = Alarm_struct.dwSize
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
            print(pNum)
            STRUCT = NET_DVR_ALARM_ISAPI_PICDATA * pNum
            PicStruct = cast(Alarm_struct.pPicPackData, POINTER(STRUCT)).contents
            for nPicIndex in range(pNum):
                nSize = PicStruct[nPicIndex].dwPicLen
                print(nSize)
                if nSize != 0:
                    buffInfo = string_at(PicStruct[nPicIndex].pPicData, nSize)
                    strName = str(PicStruct[nPicIndex].szFilename)
                    single_alrm['PicName'] = strName
                    sFileName = ('../../pic/ISAPI_Pic[%d].jpg' % nPicIndex)
                    with open(sFileName, 'wb') as fpPic:
                        fpPic.write(buffInfo)

    alarm_info.append(single_alrm)
    # print(alarm_info[-1])
    tt.insert(tkinter.END, alarm_info[-1])
    tt.insert(tkinter.END, '\r\n---------------\r\n')
    return True

# 回调函数定义，需要是全局的
setdvrmsg_callback_func = MSGCallBack_V31(g_fMessageCallBack_Alarm)

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
    sdk.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)

    # 通用参数配置
    sdkCfg = NET_DVR_LOCAL_GENERAL_CFG()
    sdkCfg.byAlarmJsonPictureSeparate = 1
    sdk.NET_DVR_SetSDKLocalCfg(17, byref(sdkCfg))

    # 设置报警回调函数
    sdk.NET_DVR_SetDVRMessageCallBack_V31(setdvrmsg_callback_func, None)

    # 初始化用户id, 在调用正常是程序一般返回正数，故初始化一个负数
    UserID = c_long(-1)

    # 用户注册设备
    # c++传递进去的是byte型数据，需要转成byte型传进去，否则会乱码
    # 登录参数，包括设备地址、登录用户、密码等
    struLoginInfo = NET_DVR_USER_LOGIN_INFO()
    struLoginInfo.bUseAsynLogin = 0  # 同步登录方式
    struLoginInfo.sDeviceAddress = bytes("10.17.35.41", "ascii")  # 设备IP地址
    struLoginInfo.wPort = 8000  # 设备服务端口
    struLoginInfo.sUserName = bytes("admin", "ascii")  # 设备登录用户名
    struLoginInfo.sPassword = bytes("abcd1234", "ascii")  # 设备登录密码
    struLoginInfo.byLoginMode = 0

    # 设备信息, 输出参数
    struDeviceInfoV40 = NET_DVR_DEVICEINFO_V40()
	
    UserID = sdk.NET_DVR_Login_V40(byref(struLoginInfo), byref(struDeviceInfoV40))
    if UserID < 0:
        print("Login failed, error code: %d" % sdk.NET_DVR_GetLastError())
        sdk.NET_DVR_Cleanup()
    else:
        print('登录成功，设备序列号：%s' % str(struDeviceInfoV40.struDeviceV30.sSerialNumber, encoding = "utf8"))

    # 布防句柄
    handle = c_long(-1)
    sdk.NET_DVR_SetupAlarmChan_V41.restype = c_long

    # 启用布防
    struAlarmParam = NET_DVR_SETUPALARM_PARAM()
    struAlarmParam.dwSize = sizeof(struAlarmParam)
    struAlarmParam.byAlarmInfoType = 1  # 智能交通报警信息上传类型：0- 老报警信息（NET_DVR_PLATE_RESULT），1- 新报警信息(NET_ITS_PLATE_RESULT)
    struAlarmParam.byDeployType = 1 # 布防类型：0-客户端布防，1-实时布防
    handle = sdk.NET_DVR_SetupAlarmChan_V41(UserID, byref(struAlarmParam))
    if handle < 0:
        print("NET_DVR_SetupAlarmChan_V41 失败, error code: %d" % sdk.NET_DVR_GetLastError())
        sdk.NET_DVR_Logout(UserID)
        sdk.NET_DVR_Cleanup()

    # show Windows
    win.mainloop()
    # 等待接收报警信息，如果需要一直接收事件，程序进程需要一直运行，不要退出

    # 撤销布防，退出程序时调用
    sdk.NET_DVR_CloseAlarmChan_V30(handle)
    # 注销用户，退出程序时调用
    sdk.NET_DVR_Logout(UserID)
    # 释放SDK资源，退出程序时调用
    sdk.NET_DVR_Cleanup()
