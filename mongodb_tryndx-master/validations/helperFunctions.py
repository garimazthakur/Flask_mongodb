NOT_ALLOWED = ["", None, True, False, [], {}]


def arrayLength(arr, length):
    if len(arr) == length:
        return True
    else:
        return False


def checkFields(staticFields, dataFields):
    requiredfields = list(set(staticFields) - set(dataFields))
    extraFields = list(set(dataFields) - set(staticFields))
    if len(requiredfields) == 0:
        return (extraFields[0] + " is not alllowed")
    else:
        return (requiredfields[0] + " is required")


def notEmpty(data):
    resp = {"status": True}
    for k in data:
        if data[k] in NOT_ALLOWED:
            resp = {"status": False, "message": k + " should not be Empty"}
            break
    return resp


def strLength(data, keysList):
    for key in keysList:
        if data.get(key) != None:
            if len(data.get(key)) < keysList[key]["min"]:
                return {"status": False, "message": key + " should be greater than " + str(keysList[key]["min"]-1) + " in length"}
            elif len(data.get(key)) > keysList[key]["max"]:
                return {"status": False, "message": key + " should be lesser than " + str(keysList[key]["max"]+1) + " in length"}
            else:
                return {"status": True}


def count_range_in_list(li, min, max):
    count = 0
    for x in li:
        if min < x <= max:
            count += 1
    return count


