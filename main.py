import csv
import requests
from bs4 import BeautifulSoup
import os
import datetime
import shutil
import sys


MY_LIBRARY = sys.argv[1]
GOODREADS_EXPORT_FILE = sys.argv[2]

def copy_lib(name):
    '''Function to take a file (in this case anticipated to be a library file, append dd/mm/yyyy/hh/mm to the title to back it up'''
    now=datetime.datetime.today()
    head = os.path.splitext(name)[0]
    back_up = head + ' date '+ str(now.year) + ' ' + str(now.month) + ' ' + str(now.day) + ' time ' + str(now.hour) + ' ' + str(now.minute) + '.csv'
    shutil.copy(name, back_up)
    print('{} copied to {}'.format(name, back_up))

try:
    copy_lib(MY_LIBRARY)
except:
    pass



def verify_goodreads(goodread):
    '''''Goodreads exports have x columns. This just tests to confirm no amendments have been made'''
    print('Verifying "{}"....'.format(goodread))
    with open(goodread, newline='') as source:
        reader = csv.reader(source)
        z = reader.__next__()
        if z.__len__() == 31:
            return True
        else:
            return False

def goodreads_to_lib(goodreads):
    '''Goodreads exports do not have an ISBN column but the library file does. This function takes a goodreads export CSV file and //
    adds a separate ISBN column to the header and a blank record to each row'''
    print('Converting "{}" to add in a "Dewey" coumn.'.format(goodreads))
    with open('temp_file.csv', 'w', newline ='') as tmp:
        temp_writer = csv.writer(tmp, quoting=csv.QUOTE_ALL)
        with open(goodreads, newline='') as source:
            reader = csv.reader(source)
            z = reader.__next__()
            z.append('Dewey')
            temp_writer.writerow(z)
            for item in reader:
                item.append('Unknown')
                temp_writer.writerow(item)
    os.remove(goodreads)
    os.rename('temp_file.csv', goodreads)
    print('"{}" now contains a "Dewey" column with the "Dewey" entries marked as "Unknown"'.format(goodreads))

#goodreads_to_lib(MY_LIBRARY)

def get_ISBN(row):
    '''Takes a row from a Goodreads CSV file and returns the ISBN number for the entry'''
    return (row[5].strip('=')).strip('"')

def obtain_Dewey(soup):
    '''Takes a soup object and returns the Dewey reference for the relevant book, or None if there is not one'''
    try:
        Dewey = soup.find_all(id='classSummaryData')[0].find_all('td')[1].text
    except:
        return None
    return Dewey

#write a function taking two arguments; function iterates over each row of the first and, if that book isn't in the second, adds it to the second

def get_new_bookids(x, y):
    '''Returns a list of book IDs which are in x and not in y'''
    print('Getting list of BookIDs which are in {} and not in {}'.format(x,y))
    dump = open(x, newline='')
    return_array = []
    dump_array = []
    libr_array = []
    libr = open(y, newline='')
    dump_reader = csv.reader(dump)
    #dump_reader.__next__()
    libr_reader = csv.reader(libr)
    #libr_reader.__next__()
    for dump_row in dump_reader:
        dump_array.append(dump_row[0])
    for libr_row in libr_reader:
        try:
            libr_array.append(libr_row[0])
        except:
            pass
    for item in dump_array:
        if item not in libr_array:
            print("Adding {} to {}".format(item, y))
            return_array.append(item)
        else:
            print("{} is already in {}".format(item, y))
    return return_array        
       
def extract_book(bookid, file):
    '''Takes a bookid and returns the record extracted from the file'''
    with open(file, newline='') as f:
        file_reader = csv.reader(f)
        for line in file_reader:
            if line[0] == bookid:
                return line

def insert_book_record(bookid, source, dest):
    '''Take a bookid, gets the record from source and puts into dest'''
    record = extract_book(bookid, source)
    with open(dest, 'a', newline='') as f:
        dest_writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        print('Writing {} to "{}"....'.format(record[1], dest))
        #print("{} has {} entries".format(record[1], record.__len__()))
        dest_writer.writerow(record)

#print(get_new_bookids('test.csv', 'dest.csv'))    
#extract_book('31297813', 'test.csv')

def ISBN_to_Dewey(ISBN):
    '''Takes an ISBN and converts to a Dewey reference'''
    URL = 'http://classify.oclc.org/classify2/ClassifyDemo?search-standnum-txt={}&startRec=0'.format(ISBN)
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    if test_for_result(soup) == False:
        return False
    if obtain_Dewey(soup) != None:
        print('Got Dewey first time from ISBN.')
        return obtain_Dewey(soup)
    URL = 'http://classify.oclc.org{}'.format(soup.find(id='results-table').tbody.td.a['href'])
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    if obtain_Dewey(soup) != None:
        print('Got Dewey second time from ISBN.')
        return obtain_Dewey(soup)
    print("Couldn't get Dewey")
    return False

def test_for_result(soup):
    if soup.find(class_='error') != None:
        return False
    return True

def title_to_Dewey(title):
    '''Takes a title and converts to a Dewey reference'''
    URL = 'http://classify.oclc.org/classify2/ClassifyDemo?search-title-txt={}&startRec=0'.format(title)
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    if test_for_result(soup) == False:
        return False    
    if obtain_Dewey(soup) != None:
        print('Got Dewey first time from title.')
        return obtain_Dewey(soup)
    URL = 'http://classify.oclc.org{}'.format(soup.find(id='results-table').tbody.td.a['href'])
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    if obtain_Dewey(soup) != None:
        print('Got Dewey second time from title.')
        return obtain_Dewey(soup)
    return False    

#Export Goodreads to folder as 'goodreads.csv'

#Confirm it is actually a goodreads file

if verify_goodreads(GOODREADS_EXPORT_FILE) == True:
    print("'{}' appears ot be a goodreads export file".format(GOODREADS_EXPORT_FILE))
    #Update goodreads.csv to my library format
    goodreads_to_lib(GOODREADS_EXPORT_FILE)    
    #Check if this new export has any files not in my library and, if so, add them to the my library file at the same time obtaining the ISBN and adding that too
    additions = get_new_bookids(GOODREADS_EXPORT_FILE, MY_LIBRARY)
    with open(MY_LIBRARY, 'a', newline='') as f:
        f.write('\n')
    #Add these to the MY_LIBRARY file
    for bookid in additions:
        record = extract_book(bookid, GOODREADS_EXPORT_FILE)
        with open(MY_LIBRARY, 'a', newline='') as f:
            dest_writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            print('Writing {} to "{}"....'.format(record[1], MY_LIBRARY))
            dest_writer.writerow(record)
else:
    print('File supplied was not a Goodreads export')
    quit()

with open('new_lib.csv', 'w', newline='') as new_lib:
    new_lib_writer = csv.writer(new_lib, quoting=csv.QUOTE_ALL)
    with open(MY_LIBRARY, newline='') as f:
        lib_reader = csv.reader(f)
        for item in lib_reader:
            try:
                if item[31] == 'Unknown':
                    ISBN =  item[5].strip('=').strip('"')
                    if (ISBN == ''):
                        print('Getting Dewey number for {}...'.format(item[1]))
                        Dewey_from_title = title_to_Dewey(item[1])
                        if Dewey_from_title != False:
                            item.remove(item[31])
                            item.append(Dewey_from_title)
                            new_lib_writer.writerow(item)
                            continue
                        else:
                            new_lib_writer.writerow(item)
                            continue                        
                    else:
                        print('Getting Dewey number for {}...'.format(item[1]))
                        Dewey_from_ISBN = ISBN_to_Dewey(ISBN)
                        if Dewey_from_ISBN != False:
                            item.remove(item[31])
                            item.append(Dewey_from_ISBN)
                            new_lib_writer.writerow(item)
                            continue
                        else:
                                new_lib_writer.writerow(item)
                                continue              
                else:
                    print('Already have Dewey number for {}.'.format(item[1]))
                    new_lib_writer.writerow(item)
                    continue                    
            except:
                continue

os.remove(MY_LIBRARY)
shutil.copy('new_lib.csv', MY_LIBRARY)


