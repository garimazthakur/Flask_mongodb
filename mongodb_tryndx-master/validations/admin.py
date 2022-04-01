from constants import codes, messages
from . import helperFunctions as HF
import re


def validateAdmin(data,schema):
  err_log = {}
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
          #err.append("Please enter proper right datatype for {}".format(i))
          test = str(test)
        if len(test) < constraints['min']:
          if i == 'phone':
            err.append("Phone number needs to be more than 7 digits")
          else:
            err.append("{} length must be greater than {}".format(i,constraints['min']))
        if len(test) > constraints['max']:
          if i == 'phone':
            err.append("Phone number needs to be less than 15 digits")
          else:
            err.append("{} length must be less than {}".format(i,constraints['max']))
        if re.search(constraints["regex"], test) is None:
          err.append("{} is not valid".format(i))
      if err != [] and i not in err_log:
        err_log[i] = err
  return err_log


def validateSignup(data):
    dataFields = list(set(data.keys()))
    dataFields.sort()
    staticFields = ['firstName', 'lastName', 'phone',
                    'countryCode', 'profilePic', 'password']
    staticFields.sort()
    if(dataFields == staticFields):
        isEmpty = HF.notEmpty(data)
        if(isEmpty["status"] == False):
            return {"status": codes.BAD_REQUEST, "message": isEmpty["message"]}
        lengths = {
            "firstName": {
                "min": 10,
                "max": 20
            }
        }
        isLengthsValid = HF.strLength(data, lengths)
        if(isLengthsValid["status"] == False):
            return {"status": codes.BAD_REQUEST, "message": isLengthsValid["message"]}
        return {"status": codes.OK, "data": {}, "message": messages.VALIDATION_COMPLETED}
    else:
        return {"status": codes.BAD_REQUEST, "message": HF.checkFields(staticFields, dataFields)}


def isUnique(db, data):
    unique_fields = ['phone','email']
    keys = list(data.keys())
    dup = []
    for i in keys:
        if i in unique_fields:
            doc = db.admin.find_one({i:data[i]})
            if doc is not None:
                dup.append(i)
    if dup == []:
        return True
    else:
        return {"res":dup}