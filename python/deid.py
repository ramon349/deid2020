import re
import sys
import numpy as np 

age_pattern = r'\b\d\d\b'
age_reg  = re.compile(age_pattern)
age_hint= r'(year|old|yo|y\.o)'
age_hint_reg = re.compile(age_hint,flags=re.IGNORECASE)
from nltk.tokenize import sent_tokenize 


def is_close(age_candidate,age_hint): 
    """  We have age_candidate matches. We will verify are truly patient ages by mesuring
    how close they are to age words such as year, old, "year old" and so forth. 

    """
    distance_threshold = 6
    age_end = age_candidate.span()[1]
    hint_start = age_hint.span()[1]
    if  np.abs(age_end - hint_start) <= distance_threshold: 
        return True
    else: 
        return False


## our goal here would be to tokenize words and see the inclusion of certain key words
def search_lines(chunk): 
    outputs = list()  
    match = list(age_reg.finditer(chunk) )
    exist = list(age_hint_reg.finditer(chunk) ) 
    offset = 29
    if match and len(exist) >0 : 
        for k in match:  
            closeness = [is_close(k,w) for w in exist ]
            if not np.any(closeness) :
                continue
            a,b = k.span() 
            print(chunk[a-30:b+30] )
            start=  k.start() -  offset 
            end =  k.end()  - offset
            result = str(start) + ' ' + str(start)  +' '+ str(end) 
            outputs.append(result)
    return outputs
def check_for_age(patient,note,chunk, output_handle):
    """
    Inputs:
        - patient: Patient Number, will be printed in each occurance of personal information found
        - note: Note Number, will be printed in each occurance of personal information found
        - chunk: one whole record of a patient
        - output_handle: an opened file handle. The results will be written to this file.
            to avoid the time intensive operation of opening and closing the file multiple times
            during the de-identification process, the file is opened beforehand and the handle is passed
            to this function. 
    Logic:
        We apply 2 searches on the provided input chunk. 1 for potential age numbers as noted by 2  digits
        Our second search is for words that are age related such as "year old,y.o " see age_hint var 
        for more. For all the age matches we only write the ones that are 6 characters away form an 
        age_hint match. 
    """
    output_handle.write('Patient {}\tNote {}\n'.format(patient,note))
    outputs = list()  
    age_candidates = list(age_reg.finditer(chunk) )
    age_hints = list(age_hint_reg.finditer(chunk) ) 
    offset = 29 # index offset for compatibility with perl scripts 
    if age_candidates and len(age_hints) >0 : 
        for k in age_candidates:  
            closeness = [is_close(k,hint) for hint in age_hints ]
            #if there are no close age terms we skip 
            if not np.any(closeness) :
                continue
            #these 2 lines are to show what labeled positive classes are 
            #a,b = k.span() 
            #print(chunk[a-30:b+30] )
            start=  k.start() -  offset 
            end =  k.end()  - offset
            result = str(start) + ' ' + str(start)  +' '+ str(end) 
            output_handle.write(result+'\n')
            
            
def deid_age(text_path= 'id.text', output_path = 'phone.phi'):
    """
    Inputs: 
        - text_path: path to the file containing patient records
        - output_path: path to the output file.
    
    Outputs:
        for each patient note, the output file will start by a line declaring the note in the format of:
            Patient X Note Y
        then for each age  found, it will have another line in the format of:
            start start end
        where the start is the start position of the detected age string, and end is the detected
        end position of the string both relative to the start of the patient note.
        If there is no age detected in the patient note, only the first line (Patient X Note Y) is printed
        to the output
    """
    # start of each note has the patter: START_OF_RECORD=PATIENT||||NOTE||||
    # where PATIENT is the patient number and NOTE is the note number.
    start_of_record_pattern = '^start_of_record=(\d+)\|\|\|\|(\d+)\|\|\|\|$'

    # end of each note has the patter: ||||END_OF_RECORD
    end_of_record_pattern = '\|\|\|\|END_OF_RECORD$'
    counter =1 
    # open the output file just once to save time on the time intensive IO
    with open(output_path,'w+') as output_file:
        with open(text_path,'r') as text:
            # initilize an empty chunk. Go through the input file line by line
            # whenever we see the start_of_record pattern, note patient and note numbers and start 
            # adding everything to the 'chunk' until we see the end_of_record.
            chunk = ''
            for line in text:
                record_start = re.findall(start_of_record_pattern,line,flags=re.IGNORECASE)
                if len(record_start):
                    patient, note = record_start[0]
                chunk += line

                # check to see if we have seen the end of one note
                record_end = re.findall(end_of_record_pattern, line,flags=re.IGNORECASE)

                if len(record_end) :
                    # Now we have a full patient note stored in `chunk`, along with patient numerb and note number
                    # pass all to check_for_phone to find any phone numbers in note.
                    print(f"----Start patient: {patient}----")
                    check_for_age(patient,note,chunk.strip(), output_file)
                    counter = counter + 1  
                    # initialize the chunk for the next note to be read
                    chunk = ''
                
if __name__== "__main__":
    deid_age(sys.argv[1], sys.argv[2])