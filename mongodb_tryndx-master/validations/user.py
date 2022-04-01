import re
import json
import datetime

def validateUser(data,schema):
  err_log = {}
  data = dict(data)
  for i in list((data.keys())):
    err = []
    if i in schema:
      test = data[i]
      constraints = schema[i]
      if test == '' and constraints['required']==True:
        if i == 'phone':
          pass
        else:
          err.append('Please Enter {}'.format(i))
      else:
        if not isinstance(test, str):
          err.append("Please enter proper right datatype for {}".format(i))
          test = str(test)
        if len(test) < constraints['min']:

          if i == 'phone':
            err.append("Phone number needs to be of 10 digits")
          else:
            err.append("{} length must be greater than {}".format(i,constraints['min']))
        if len(test) > constraints['max']:
          if i == 'phone':
            err.append("Phone number needs to be of 10 digits")
          else:
            err.append("{} length must be less than {}".format(i,constraints['max']))
        if re.search(constraints["regex"], test) is None:
          err.append("{} is not valid".format(i))
      if err != [] and i not in err_log:
        err_log[i] = err
  return err_log



def isUnique(db, data, UID=None, social=None):
  dup = []
  if social == True:
    doc1 = db.users.find_one({"email": data['username']})
    if doc1:
      dup.append('Email')

  unique_fields = ['phone', 'email', 'username']
  keys = list(data.keys())
  for i in keys:
    if i in unique_fields:
      doc = db.users.find_one({"UID":{"$ne":UID}, i: data[i]})
      if doc is not None:
        if i == 'phone':
          dup.append('Phone')
        elif i == 'email':
          dup.append('Email')
        elif i == 'username':
          dup.append('Username')
  if dup == []:
    return True
  else:
    return dup
  
def validateCardDetails(setObj):
  log = []
  if len(setObj['card_number']) != 16:
    log.append('Card Number')
  if len(setObj['CVV']) != 3:
    log.append('CVV')
  if len(setObj['card_holder_name']) > 50 or len(setObj['card_holder_name']) < 2:
    log.append('Card Holder Name')

  if log == []:
    return True
  else:
    return log


