#!/usr/bin/env python

import os
import pathlib
import queue
import sys
import _thread
import threading
import time


SYSTEM_EXIT_CODE = { 'Success': 0,
                     'Failure': 1 }

BUFFER_SIZE = 1000 # in bytes

QUEUE = queue.Queue()


class Exclusion(Exception):
    # Empty
    pass


class Status(threading.Thread):
    STATUS_TEMPLATE = 'Progress: {Progress:6.2f}% (Elapsed: {E_Hour:02}:{E_Min:02}:{E_Sec:02})'
    
    
    def __init__(self, file_size_, mutex_):
        super().__init__()
        
        self._FILE_SIZE = file_size_
        self._MUTEX = mutex_
           
        
    def Status(self, status_current_, status_previous_):
        with self._MUTEX:
            print('\b' * len(status_previous_),
                  end='')
            print(status_current_,
                  end='',
                  flush=True)
    
    
    def run(self):
        amount_compared = 0
        status_current = ''
        
        #TIME_START = datetime.datetime.now()
        TIME_START = time.time()
        
        while True:
            try:
                amount_compared += QUEUE.get(block=False)
                
            except queue.Empty:
                # Empty
                pass
            
            TIME_DELTA = time.gmtime(time.time() - TIME_START)
            
            status_previous = status_current
            status_current = __class__.STATUS_TEMPLATE.format(Progress=(amount_compared / self._FILE_SIZE * 100),
                                                              E_Hour=TIME_DELTA.tm_hour,
                                                              E_Min=TIME_DELTA.tm_min,
                                                              E_Sec=TIME_DELTA.tm_sec)
            
            self.Status(status_current, status_previous)
            
            if amount_compared < self._FILE_SIZE:
                time.sleep(1.0)
            
            else:
                break
            
            
def Compare(file_1_, file_2_):
    FILE_SIZES = ( pathlib.Path(file_1_).stat().st_size,
                   pathlib.Path(file_2_).stat().st_size )
    
    print('[File 1]: {0} ({1:,} bytes)'.format(file_1_, FILE_SIZES[0]))
    print('[File 2]: {0} ({1:,} bytes)'.format(file_2_, FILE_SIZES[1]))
    
    if FILE_SIZES[0] != FILE_SIZES[1]:
        print('Results: Unmatched. (Different file sizes.)')
        
        raise Exclusion()
    
    FILE_SIZE = FILE_SIZES[0]
    
    FILES = ( open(file_1_, 'rb'),
              open(file_2_, 'rb') )
    
    STATUS = Status(FILE_SIZE, _thread.allocate_lock())
    STATUS.daemon = True
    
    STATUS.start()
    
    pointer = 0
    
    try:
        while True:
            DATA = [FILE.read(BUFFER_SIZE) for FILE in FILES]
            DATA_SIZE_READ = len(DATA[0])
        
            if 0 < DATA_SIZE_READ:
                for (P, (U, V)) in enumerate(zip(DATA[0], DATA[1])):
                    if U != V:
                        print()
                        print('Results: Unmatched. ([File 1]={0}; [File 2]={1} at byte {2:,}.)'.format(hex(U),
                                                                                                   hex(V),
                                                                                                   pointer + P),
                              flush=True)
                        
                        raise Exclusion()
                    
                else:
                    pointer += DATA_SIZE_READ
                    
                    amount_compared = DATA_SIZE_READ
                    
                    try:
                        amount_compared += QUEUE.get(block=False)
                        
                    except queue.Empty:
                        # Empty
                        pass
                        
                    QUEUE.put(amount_compared)
                    
            else:
                # Empty
                pass
            
            if DATA_SIZE_READ < BUFFER_SIZE:
                STATUS.join()
                
                print()
                print('Matched',
                      flush=True)
                
                break
            
            else:
                # Empty
                pass
    
    except Exclusion:
        # Empty
        pass
    
    finally:
        for FILE in FILES:
            if FILE is not None:
                FILE.close()
                
            else:
                # Empty
                pass


def Usage():
    print('usage: {0} <file_1> <file_2>'.format(os.path.basename(__file__)))
    
    
def main(argv_):
    result = SYSTEM_EXIT_CODE['Failure']

    if len(argv_) != 2:
        Usage()
        
        raise Exclusion()
    
    try:
        Compare(argv_[0], argv_[1])
        
        result = SYSTEM_EXIT_CODE['Success']
        
    except Exclusion:
        # Empty
        pass
    
    except Exception as ex_:
        print(ex_,
              file=sys.stderr,
              flush=True)
    
    return result


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    
    except Exclusion:
        #  Empty
        pass
    
    except SystemExit:
        # Empty
        pass
    
    except Exception as ex_:
        print(ex_,
              file=sys.stderr,
              flush=True)
        
        sys.exit(SYSTEM_EXIT_CODE['Failure'])