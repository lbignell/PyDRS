########################################################
#
#  Makefile for drsosc, drscl and drs_exam 
#  executables under linux
#
#  Requires wxWidgets 2.8.9 or newer
#
########################################################

OS           = OS_LINUX
DRS_DIR      = /home/pi/Downloads/drs-5.0.6
INCDIR       = $(DRS_DIR)/include
SRCDIR       = $(DRS_DIR)/src

CFLAGS        = -g -O2 -Wall -Wuninitialized -fPIC -I$(INCDIR) -I/usr/local/include -D$(OS) -DHAVE_USB -DHAVE_LIBUSB10
LDFLAGS       = -shared
LIBS          = -lpthread -lutil -lusb-1.0

CPP_OBJ       = DRS.o averager.o
OBJECTS       = musbstd.o mxml.o strlcpy.o


all: libdrs

libdrs: $(OBJECTS) DRS.o averager.o libdrs.o
	$(CXX) $(CFLAGS) $(LDFLAGS) $(OBJECTS) DRS.o averager.o libdrs.o -o libdrs.so $(LIBS)

libdrs.o: libdrs.cpp libdrs.h
	$(CXX) $(CFLAGS) -c $<


$(CPP_OBJ): %.o: $(SRCDIR)/%.cpp $(INCDIR)/%.h $(INCDIR)/mxml.h $(INCDIR)/DRS.h
	$(CXX) $(CFLAGS) $(WXFLAGS) -c $<

$(OBJECTS): %.o: $(SRCDIR)/%.c $(INCDIR)/mxml.h $(INCDIR)/DRS.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f *.o drs_exam

