#include <math.h>

#ifdef _MSC_VER

#include <windows.h>

#elif defined(OS_LINUX)

#define O_BINARY 0

#include <unistd.h>
#include <ctype.h>
#include <sys/ioctl.h>
#include <errno.h>

#define DIR_SEPARATOR '/'

#endif

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "strlcpy.h"
#include "DRS.h"

#include "libdrs.h"
/*------------------------------------------------------------------*/

void* drs_create(){
    return (void*) new DRS();
}
void drs_delete(void* drs){
    delete (DRS*)drs;
}

//void* drs_create(){
//    return (void*) new DRSBoard();
//}
//void drs_delete(void* drs){
//    delete (DRSBoard*)drs;
//}


int drs_getNumberOfBoards(void* drs){
    return ((DRS*)drs)->GetNumberOfBoards();
}
int drs_getFirmwareVersion(void* drs){
    return (((DRS*)drs)->GetBoard(0))->GetFirmwareVersion();
}
int drs_getBoardSerialNumber(void* drs){
    return (((DRS*)drs)->GetBoard(0))->GetBoardSerialNumber();
}
void* drs_getBoard(void* drs, int i){
    return (void*) ((DRS*)drs)->GetBoard(i);
}
int drs_init(void* drs){
    return (((DRS*)drs)->GetBoard(0))->Init();
}
int drs_setFrequency(void* drs,int freq, bool wait){
    return (((DRS*)drs)->GetBoard(0))->SetFrequency(freq,wait);
}
double drs_getNominalFrequency(void* drs){
    return (((DRS*)drs)->GetBoard(0))->GetNominalFrequency();
}
double drs_getTrueFrequency(void* drs){
    return (((DRS*)drs)->GetBoard(0))->GetTrueFrequency();
}
int drs_setTranspMode(void* drs,int flg){
    return (((DRS*)drs)->GetBoard(0))->SetTranspMode(flg);
}
int drs_setInputRange(void* drs,double center){
    return (((DRS*)drs)->GetBoard(0))->SetInputRange(center);
}
double drs_getInputRange(void* drs){
    return ((DRSBoard*)drs)->GetInputRange();
}
int drs_enableTcal(void* drs,int freq, int level=0, int phase=0){
    return (((DRS*)drs)->GetBoard(0))->EnableTcal(freq, level, phase);
}
int drs_getBoardType(void* drs){
    return (((DRS*)drs)->GetBoard(0))->GetBoardType();
}
int drs_enableTrigger(void* drs,int flag1, int flag2){
    return (((DRS*)drs)->GetBoard(0))->EnableTrigger(flag1, flag2);
}
int drs_setTriggerSource(void* drs,int source){
    return (((DRS*)drs)->GetBoard(0))->SetTriggerSource(source);
}
int drs_getTriggerSource(void* drs){
    return ((DRSBoard*)drs)->GetTriggerSource();
}
int drs_setTriggerPolarity(void* drs,bool negative){
    return (((DRS*)drs)->GetBoard(0))->SetTriggerPolarity(negative);
}
int drs_setTriggerLevel(void* drs,double value){
    return (((DRS*)drs)->GetBoard(0))->SetTriggerLevel(value);
}
int drs_setIndividualTriggerLevel(void* drs,int channel, double voltage){
    return (((DRS*)drs)->GetBoard(0))->SetIndividualTriggerLevel(channel, voltage);
}
int drs_setTriggerDelayNs(void* drs,int delay){
    return (((DRS*)drs)->GetBoard(0))->SetTriggerDelayNs(delay);
}

double drs_getTriggerDelayNs(void* drs){
    return (((DRS*)drs)->GetBoard(0))->GetTriggerDelayNs();
}
int drs_startDomino(void* drs){
    return (((DRS*)drs)->GetBoard(0))->StartDomino();
}
int drs_setDominoMode(void* drs,unsigned char mode){
    return (((DRS*)drs)->GetBoard(0))->SetDominoMode(mode);
}
int drs_setDominoActive(void* drs,unsigned char mode){
    return (((DRS*)drs)->GetBoard(0))->SetDominoActive(mode);
}
int drs_isBusy(void* drs){
    return (((DRS*)drs)->GetBoard(0))->IsBusy();
}
int drs_transferWaves(void* drs,int firstChannel, int lastChannel){
    return (((DRS*)drs)->GetBoard(0))->TransferWaves(firstChannel, lastChannel);
}
int drs_getTriggerCell(void* drs,unsigned int chipIndex){
    return (((DRS*)drs)->GetBoard(0))->GetTriggerCell(chipIndex);
}
int drs_getTime(void* drs,unsigned int chipIndex, int channelIndex, int tc, float *time, bool tcalibrated=true, bool rotated=true){
    return (((DRS*)drs)->GetBoard(0))->GetTime(chipIndex, channelIndex, tc, time, tcalibrated, rotated);
}
int drs_getTime2(void* drs, int channelIndex,float *time){
    DRSBoard * b;
    b=((DRS*)drs)->GetBoard(0);
    return b->GetTime(0, channelIndex, b->GetTriggerCell(0), time);
}
int drs_getWave(void* drs,unsigned int chipIndex, unsigned char channel, float *waveform){
    return (((DRS*)drs)->GetBoard(0))->GetWave(chipIndex, channel, waveform);
}
