#include <REGX52.H>
#include <Delay.h>
#include <Timer0.h>

sbit Buzzer = P2^5;

// 定义两个全局变量，用来实时更新定时器初值
unsigned char Freq_TH;
unsigned char Freq_TL;

// 这里粘贴 Python 脚本生成的数组
unsigned char code Music_Data[] = {
       0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x04, 207,  // M5, 392Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 414,  // H3, 659Hz, 414ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x04, 207,  // M5, 392Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFC, 0x44, 414,  // H1, 523Hz, 414ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x04, 207,  // M5, 392Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 414,  // H3, 659Hz, 414ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFB, 0x04, 207,  // M5, 392Hz, 207ms
    0xFB, 0x90, 414,  // M6, 440Hz, 414ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFD, 0x09, 103,  // H3, 659Hz, 103ms
    0xFD, 0x09, 103,  // H3, 659Hz, 103ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFD, 0x82, 207,  // H5, 784Hz, 207ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFC, 0xAC, 414,  // H2, 587Hz, 414ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFD, 0x09, 103,  // H3, 659Hz, 103ms
    0xFD, 0x09, 103,  // H3, 659Hz, 103ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFD, 0x82, 207,  // H5, 784Hz, 207ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x90, 103,  // M6, 440Hz, 103ms
    0xFB, 0x04, 207,  // M5, 392Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 414,  // H3, 659Hz, 414ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFD, 0x09, 207,  // H3, 659Hz, 207ms
    0xFC, 0xAC, 207,  // H2, 587Hz, 207ms
    0xFC, 0x44, 207,  // H1, 523Hz, 207ms
    0xFB, 0x90, 207,  // M6, 440Hz, 207ms
    0xFB, 0x04, 207,  // M5, 392Hz, 207ms
    0xFB, 0x90, 414,  // M6, 440Hz, 414ms
    0x00, 0x00, 414,  // 0, 休止符, 414ms
    0xFF, 0xFF, 0   // 结束标志
};

void main()
{
    unsigned int i = 0; // 数组索引
    Timer0_Init();
    
    while(1)
    {
        // 如果遇到 0xFF，说明播放结束了，停在这里
        if(Music_Data[i] == 0xFF)
        {
            TR0 = 0; // 关闭定时器
            while(1); // 停机死循环（或者你可以让 i=0 重新播放）
        }
        
        // 读取定时器初值
        Freq_TH = Music_Data[i];
        Freq_TL = Music_Data[i+1];
        
        // 如果 TH 和 TL 都是 0，说明是休止符，关闭定时器不发声
        if(Freq_TH == 0x00 && Freq_TL == 0x00)
        {
            TR0 = 0; 
        }
        else
        {
            TR0 = 1; // 开启定时器发声
        }
        
        // 延时对应的毫秒数 (数组的第三个元素)
        Delay(Music_Data[i+2]);
        
        // 播放完一个音符后，稍微停顿一下（比如延时 5ms），让音符之间有颗粒感
        TR0 = 0;
        Buzzer = 0; // 让蜂鸣器引脚复位，防止漏电发热
        Delay(5);
        
        i += 3; // 移动到下一个音符的数据
    }
}

void Timer0_Routine() interrupt 1
{
    TH0 = Freq_TH; 
    TL0 = Freq_TL; 
    Buzzer = !Buzzer;
}