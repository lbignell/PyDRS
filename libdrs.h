
#ifdef _MSC_VER

// for windows
//#ifdef LIBDRS_EXPORTS
#define LIBDRS_API //__declspec(dllexport) 
//#else
//#define LIBDRS_API __declspec(dllimport) 
//#endif

# else
#define LIBDRS_API
#endif



#ifdef __cplusplus
extern "C" {
#endif
    LIBDRS_API void* drs_create(void);
    LIBDRS_API void drs_delete(void* drs);
    LIBDRS_API int drs_getNumberOfBoards(void* drs);
    LIBDRS_API void* drs_getBoard(void* drs, int i);
	LIBDRS_API int drs_getFirmwareVersion(void* drs);
	LIBDRS_API int drs_getBoardSerialNumber(void* drs);
	LIBDRS_API int drs_init(void* drs);
    LIBDRS_API int drs_setFrequency(void* drs,int freq, bool wait);
    LIBDRS_API double drs_getNominalFrequency(void* drs);
    LIBDRS_API double drs_getTrueFrequency(void* drs);
    LIBDRS_API int drs_setTranspMode(void* drs,int flg);
    LIBDRS_API int drs_setInputRange(void* drs,double center);
	LIBDRS_API double drs_getInputRange(void);
    LIBDRS_API int drs_enableTcal(void* drs,int freq, int level, int phase);
	LIBDRS_API int drs_getBoardType(void* drs);
	LIBDRS_API int drs_enableTrigger(void* drs,int flag1, int flag2);
	LIBDRS_API int drs_setTriggerSource(void* drs,int source);
	LIBDRS_API int drs_getTriggerSource(void* drs);
	LIBDRS_API int drs_setTriggerPolarity(void* drs,bool negative);
	LIBDRS_API int drs_setTriggerLevel(void* drs,double value);
	LIBDRS_API int drs_setIndividualTriggerLevel(void* drs,int channel, double voltage);
	LIBDRS_API int drs_setTriggerDelayNs(void* drs,int delay);
	LIBDRS_API double drs_getTriggerDelayNs(void* drs);
	LIBDRS_API int drs_startDomino(void* drs);
	LIBDRS_API int drs_setDominoActive(void* drs,unsigned char mode);
	LIBDRS_API int drs_setDominoMode(void* drs,unsigned char mode);
	LIBDRS_API int drs_isBusy(void* drs);
	LIBDRS_API int drs_transferWaves(void* drs,int firstChannel, int lastChannel);
	//LIBDRS_API int drs_getTriggerCell(unsigned char *waveforms,unsigned int chipIndex);
	LIBDRS_API int drs_getTriggerCell(void* drs,unsigned int chipIndex);
	LIBDRS_API int drs_getTime(void* drs,unsigned int chipIndex, int channelIndex, int tc, float *time, bool tcalibrated, bool rotated);
	LIBDRS_API int drs_getTime2(void* drs, int channelIndex,float *time);
	LIBDRS_API int drs_getWave(void* drs,unsigned int chipIndex, unsigned char channel, float *waveform);
#ifdef __cplusplus
}
#endif
