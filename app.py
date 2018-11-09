#!/usr/bin/env python

import urllib
import json
import os
import re
import cx_Oracle
from flask import Flask
from flask import request
import datetime as dt
import time
from flask import make_response
import cx_Oracle
import webbrowser
import time
import nexmo
import random, string
import smtplib

app = Flask(__name__)

age = None
gender = None
symptom_entity = None


@app.route('/webhook',methods=['POST'])

def webhook():
    webhook.req = request.get_json(silent=True, force=True)
    print(webhook.req)
    print(json.dumps(webhook.req, indent=4))
    if  webhook.req.get("result").get("action") == "input.welcome":
        res = Greeting(webhook.req) #Greet customer based on time
    if  webhook.req.get("result").get("action") == "CustQuery":
        res = CustQry(webhook.req) #Get Customer Query (whether they want to create a New subscription/check existing subs/change existing sub)
    if  webhook.req.get("result").get("action") == "TypeOfCust":
        res = CustType(webhook.req) #get the type of customer(new/exist) for new ask for registration| for old ask customer num
    if  webhook.req.get("result").get("action") == "TypeOfCust.Old":
        res = CustTypeOld(webhook.req) #Open registration URL for new customer
    if  webhook.req.get("result").get("action") == "TypeOfCust.Old.verify":
        res = CustOldVerfiy(webhook.req) # Take email/ph num and verify in DB and send OTP
    if  webhook.req.get("result").get("action") == "TypeOfCust.Old.OTP.Query":
        res = CustOTPQuery(webhook.req) # verifies OTP and continues with the query
    if  webhook.req.get("result").get("action") == "Create.NewOrder.Init":
        res = NewOrderInit(webhook.req) # Confirms the order
    if  webhook.req.get("result").get("action") == "Create.NewOrder.Confirm":
        res = NewOrderConfirm(webhook.req) # Confirms the order
    if  webhook.req.get("result").get("action") == "Create.NewOrder.Close":
        res = NewOrderClose(webhook.req) # places the order
    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def Greeting(req):
    result = req.get("result")
    Hour_var=dt.datetime.now().hour
    if (Hour_var < 12) :
        speech = "Hello Guest ! Good Morning , I am your Oracle Virtual Assistant .I can help you with:  1. Checking all details of your subscriptions .  2. Updating or modifying your existing order 3. Booking a new subscription for you . Please select a relevant option to continue futher."
    elif (Hour_var < 17) :
       speech = "Hello Guest ! Good Afternoon , I am your Oracle Virtual Assistant .I can help you with:  1. Checking all details of your subscriptions .  2. Updating or modifying your existing order 3. Booking a new subscription for you . Please select a relevant option to continue futher."
    else :
        speech = "Hello Guest ! Good Evening , I am your Oracle Virtual Assistant .I can help you with:  1. Checking all details of your subscriptions .  2. Updating or modifying your existing order 3. Booking a new subscription for you . Please select a relevant option to continue futher."
    print ("Response:")
    print (speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Health_Care"
  }

def CustQry(req):
    result = req.get("result")
    parameters = result.get("parameters")
    CustQry.query_type = parameters.get("Query_Type")
    if (CustQry.query_type == 'New') : #if a cust is new then ask for email address
        speech = "Type 1 in case you are a new customer  \n Type 2 if you are an existing customer"
    elif (CustQry.query_type == 'Exist') : #for existing cust ask cust#,ph# and email id
        speech = "Sure, please help me with your customer number"
    print ("Response:")
    print (speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Oracle Chatbot"
  }
  
def CustType(req):
    result = req.get("result")
    parameters = result.get("parameters")
    cust_type = parameters.get("Cust_type")
    if (cust_type == 'New') : #if a cust is new then ask for email address
        speech = "Not a problem! Let's me open the registration link for you"
        url = "http://www.google.com/"
        webbrowser.open_new_tab(url)
    elif (cust_type == 'Old') : #for existing cust ask cust#,ph# and email id
        speech = "Sure, please help me with your customer number"
    print ("Response:")
    print (speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Oracle Chatbot"
  }


def OpenUrl():
    url = "http://www.google.com/"
    webbrowser.open_new_tab(url)
    
def CustTypeOld(req):
    result = req.get("result")
    parameters = result.get("parameters")
    CustTypeOld.Accnt_Num = parameters.get("Account_Num")
    #CustTypeOld.Acc=Accnt_Num
    connection = cx_Oracle.connect('appsro/appsro@ussltcovm191.solutions.glbsnet.com:1521/VISION')
    cursor = connection.cursor()
    querystring = "select substr(replace(How_to_Contact, chr(32), ''),instr(replace(How_to_Contact, chr(32), ''),':')+1) from ( \
select account_number as Account_Number,obj.party_name as Customer_Name,sub.party_name as Contact_Name, hcp.contact_point_type || ': ' || \
       DECODE(hcp.contact_point_type, 'EMAIL', hcp.email_address, 'PHONE', hcp.phone_area_code || ' ' || hcp.phone_number, 'WEB'  , hcp.url \
                                    , 'Unknow contact Point Type ' || hcp.contact_point_type) as How_to_Contact \
  from apps.hz_cust_accounts  hca, apps.hz_parties        obj, apps.hz_relationships  rel, apps.hz_contact_points hcp, apps.hz_parties  sub \
where hca.party_id = rel.object_id and hca.party_id = obj.party_id and rel.subject_id= sub.party_id and rel.party_id = hcp.owner_table_id \
and hcp.owner_table_name   = 'HZ_PARTIES') A \
where rownum=1 \
and Account_Number="+str(CustTypeOld.Accnt_Num)+""
    cursor.execute(querystring)
    speech=cursor.fetchall()
    if cursor.rowcount > 0: 
        if cursor.rowcount == 1 :
            speech="Thanks, can I have your email address for OTP authentication"
        else :
            speech="I can see your account number "+str(CustTypeOld.Accnt_Num)+" is tagged to multiple contact numbers,please help with your email address for OTP authentication"
    else:
        speech="Sorry, looks like you have typed a worng customer number can you please provide me the correct one?"
    print ("Response:")
    print (speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Oracle Chatbot"
  }

def CustOldVerfiy(req):
    result = req.get("result")
    parameters = result.get("parameters")
    ph_no = parameters.get("phone-number")
    cust_no = CustTypeOld.Accnt_Num
    otp_key = str(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5)))
    CustOldVerfiy.OTP=otp_key
    content = 'Welcome to Oracle virtual assistant, your one time password is ' + otp_key
    #content = 'Subject: {Password Authentication}\n\n{Welcome to Oracle virtual assistant, your one time password is}' + otp_key.format(SUBJECT, TEXT)
    mail = smtplib.SMTP('smtp.gmail.com',587)
    mail.ehlo()
    mail.starttls()
    mail.login('dsarma591@gmail.com','Qwerty@123')
    mail.sendmail('dsarma591@gmail.com','dsarma591@gmail.com',content)
    mail.close()
    value="Thank you, Please provide the OTP shared on your registered Email address"
    '''connection = cx_Oracle.connect('appsro/appsro@ussltcovm191.solutions.glbsnet.com:1521/VISION')
    cursor = connection.cursor()
    querystring = "select substr(Contact_Name,0,instr(Contact_Name,' ')) from ( \
select account_number as Account_Number,obj.party_name as Customer_Name,sub.party_name as Contact_Name, hcp.contact_point_type || ': ' || \
       DECODE(hcp.contact_point_type, 'EMAIL', hcp.email_address, 'PHONE', hcp.phone_area_code || ' ' || hcp.phone_number, 'WEB'  , hcp.url \
                                    , 'Unknow contact Point Type ' || hcp.contact_point_type) as How_to_Contact \
  from apps.hz_cust_accounts  hca, apps.hz_parties        obj, apps.hz_relationships  rel, apps.hz_contact_points hcp, apps.hz_parties  sub \
where hca.party_id = rel.object_id and hca.party_id = obj.party_id and rel.subject_id= sub.party_id and rel.party_id = hcp.owner_table_id \
and hcp.owner_table_name   = 'HZ_PARTIES') A \
where rownum=1 and substr(replace(How_to_Contact, chr(32), ''),instr(replace(How_to_Contact, chr(32), ''),':')+1)='"+str(ph_no)+"' \
and Account_Number="+str(cust_no)+""
    cursor.execute(querystring)
    speech=cursor.fetchall()
    value_intrm=str(speech[0])
    if cursor.rowcount > 0:    
        client = nexmo.Client(key='718b0956', secret='zm7FU6GIIAuAFlQB')
        client.send_message({
        'from': 'Deloitte_TMT',
        'to': 918904424106,
        'text': 'Welcome to Oracle virtual assistant, your one time password is '+otp_key,
            })
        value="Thanks "+value_intrm[2:-3]+" Please provide the OTP shared on your registered mobile number in format <OTP number>"
    else:
        value="Sorry, your customer number doesn't exist in our system can you please try again?"'''
    print(value)
    return {
    "speech": value,
    "displayText": value,
    "source": "Oracle Chatbot"
  }

def CustOTPQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    User_OTP = parameters.get("any")
    #parameters.get("number")
    Chat_OTP = CustOldVerfiy.OTP
    connection = cx_Oracle.connect('apps/apps123@ussltcovm553.solutions.glbsnet.com:1521/VISION')
    cursor = connection.cursor()
    querystring = "select substr(Contact_Name,0,instr(Contact_Name,' ')) from ( \
select account_number as Account_Number,obj.party_name as Customer_Name,sub.party_name as Contact_Name, hcp.contact_point_type || ': ' || \
       DECODE(hcp.contact_point_type, 'EMAIL', hcp.email_address, 'PHONE', hcp.phone_area_code || ' ' || hcp.phone_number, 'WEB'  , hcp.url \
                                    , 'Unknow contact Point Type ' || hcp.contact_point_type) as How_to_Contact \
  from apps.hz_cust_accounts  hca, apps.hz_parties        obj, apps.hz_relationships  rel, apps.hz_contact_points hcp, apps.hz_parties  sub \
where hca.party_id = rel.object_id and hca.party_id = obj.party_id and rel.subject_id= sub.party_id and rel.party_id = hcp.owner_table_id \
and hcp.owner_table_name   = 'HZ_PARTIES') A \
where rownum=1 and  Account_Number="+str(CustTypeOld.Accnt_Num)+""
    cursor.execute(querystring)
    speech=cursor.fetchall()
    CustOTPQuery.value_intrm=str(speech[0])
    print(Chat_OTP) #string value
    print("------")
    print(User_OTP) #Int Value
    print ("OTP Response:" )
    if str(User_OTP) == Chat_OTP :
        if (CustQry.query_type == 'New') :
            speech="Thanks "+CustOTPQuery.value_intrm[2:-3]+"! I have verified your details. Type 1 if you like to order Internet Modem. Type 2 for ordering Cisco Routers and Type 3 to order 2ft Cable"
        else :
            speech="Verified!"
    else :
        speech= CustOTPQuery.value_intrm[2:-3]+" it's not a correct OTP, can you please try again?"
    print(speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Health_Care"
  }
  
def NewOrderInit(req):
    result = req.get("result")
    parameters = result.get("parameters")
    NewOrderInit.Item = parameters.get("NewOrder")
    connection = cx_Oracle.connect('apps/apps123@ussltcovm553.solutions.glbsnet.com:1521/VISION')
    cursor = connection.cursor()
    querystring = "SELECT distinct qpl.operand list_price FROM mtl_system_items_b items, \
    qp_pricing_attributes price_attrs, qp_list_lines qpl WHERE 1=1 and items.organization_id = 204 \
    and price_attrs.product_attribute_context = 'ITEM' and price_attrs.product_attribute = 'PRICING_ATTRIBUTE1' \
    and price_attrs.list_header_id = 1000 and price_attrs.product_attr_value = to_char(items.inventory_item_id) \
    and price_attrs.list_line_id = qpl.list_line_id and items.inventory_item_id \
    in (select inventory_item_id \
    from mtl_system_items_b where organization_id = 204  and upper(description) like '%"+str(NewOrderInit.Item.replace("%"," "))+"%')"
    cursor.execute(querystring)
    rst=cursor.fetchall()
    print(rst)
    list_price =re.sub('[\[\]\(\)\,\'\'<>]', '', str(rst))
    print(list_price)
    speech = "Each "+NewOrderInit.Item+" costs "+list_price+" USD, how many you would like to order?"
    print("Response:")
    print(speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Health_Care"
  } 
  
def NewOrderConfirm(req):
    result = req.get("result")
    parameters = result.get("parameters")
    NewOrderConfirm.Qty = parameters.get("Qty")
    NewOrderConfirm.Item = parameters.get("Item")
    connection = cx_Oracle.connect('apps/apps123@ussltcovm553.solutions.glbsnet.com:1521/VISION')
    cursor = connection.cursor()
    querystring = "SELECT distinct (qpl.operand * "+str(NewOrderConfirm.Qty)+") list_price FROM mtl_system_items_b items, \
    qp_pricing_attributes price_attrs, qp_list_lines qpl WHERE 1=1 and items.organization_id = 204 \
    and price_attrs.product_attribute_context = 'ITEM' and price_attrs.product_attribute = 'PRICING_ATTRIBUTE1' \
    and price_attrs.list_header_id = 1000 and price_attrs.product_attr_value = to_char(items.inventory_item_id) \
    and price_attrs.list_line_id = qpl.list_line_id and items.inventory_item_id \
    in (select inventory_item_id \
    from mtl_system_items_b where organization_id = 204  and upper(description) like '%"+str(NewOrderConfirm.Item.replace("%"," "))+"%')"
    cursor.execute(querystring)
    rst=cursor.fetchall()
    print(rst)
    total_cost=re.sub('[\[\]\(\)\,\'\'<>]', '', str(rst))
    print(total_cost)
    speech = "okay, the estimated cost of your order is "+total_cost+" USD.\
    Please confirm if I can proceed ahead and create an order for you."
    print("Response:")
    print(speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Health_Care"
  } 

def NewOrderClose(req):
    result = req.get("result")
    parameters = result.get("parameters")
    NewOrderClose.selection = parameters.get("Yes_No")
    #Account_Num = parameters.get("Account_Num")
    cust_no = CustTypeOld.Accnt_Num
    if NewOrderClose.selection == "Yes" :
        connection = cx_Oracle.connect('apps/apps123@ussltcovm553.solutions.glbsnet.com:1521/VISION')
        cursor = connection.cursor()
        querystring1 = "select distinct hca.cust_account_id from hz_cust_accounts_all hca, \
        hz_parties hp, hz_cust_acct_sites_all hcsa where hp.party_id = hca.party_id \
        and hca.cust_account_id = hcsa.cust_account_id \
        and hcsa.org_id = 204 and  hca.account_number ="+str(cust_no)
        cursor.execute(querystring1)
        rst1=cursor.fetchall()
        #cust_acc_id=str(str(str(str(rst1).replace("]","")).replace("[","")).replace("(","")).replace(")","")
        cust_acc_id=re.sub('[\[\]\(\)\,\'\'<>]', '', str(rst1))
        cust_acc_id_v = int(cust_acc_id)
        print(cust_acc_id,cust_acc_id_v)
        querystring2 = "select hcsu.site_use_id Bill_To_Site from hz_cust_site_uses_all hcsu, \
        hz_cust_acct_sites_all hcsa,hz_party_sites hps,hz_locations hl \
        where hcsu.cust_acct_site_id = hcsa.cust_acct_site_id and hcsa.party_site_id = hps.party_site_id \
        and hps.location_id = hl.location_id and hcsa.cust_account_id = "+str(cust_no)+" and hcsu.org_id = 204 \
        and hcsu.primary_flag = 'Y' and hcsu.status = 'A' and hcsu.site_use_code = 'BILL_TO' and rownum = 1"
        cursor.execute(querystring2)
        rst2=cursor.fetchall()
        bill_to_site=re.sub('[\[\]\(\)\,\'\'<>]', '', str(rst2))
        bill_to_site_v = int(bill_to_site)
        print(bill_to_site,bill_to_site_v)
        querystring3 = "select hcsu.site_use_id Ship_To_Site from hz_cust_site_uses_all hcsu, \
        hz_cust_acct_sites_all hcsa,hz_party_sites hps,hz_locations hl \
        where hcsu.cust_acct_site_id = hcsa.cust_acct_site_id \
        and hcsa.party_site_id = hps.party_site_id and hps.location_id = hl.location_id \
        and hcsa.cust_account_id = "+str(cust_no)+" and hcsu.org_id = 204 and hcsu.primary_flag = 'Y' \
        and hcsu.status = 'A' and hcsu.site_use_code = 'SHIP_TO' and rownum = 1"
        cursor.execute(querystring3)
        rst3=cursor.fetchall()
        ship_to_site=re.sub('[\[\]\(\)\,\'\'<>]', '', str(rst3))
        ship_to_site_v = int(ship_to_site)
        print(ship_to_site,ship_to_site_v)
        querystring4 = "select inventory_item_id \
        from mtl_system_items_b where organization_id = 204 and upper(description) like '%"+str(NewOrderConfirm.Item.replace("%"," "))+"'"
        print(querystring4)
        cursor.execute(querystring4)
        rst4=cursor.fetchall()
        inventory_item_id=re.sub('[\[\]\(\)\,\'\'<>]', '', str(rst4))
        print(inventory_item_id)
        inventory_item_id_v = int(inventory_item_id)
        x_errbuf = cursor.var(cx_Oracle.STRING)
        x_retcode = cursor.var(cx_Oracle.NUMBER)
        x_ordernumber = cursor.var(cx_Oracle.NUMBER)
        print(cust_acc_id,bill_to_site,ship_to_site,inventory_item_id)
        cursor.callproc('xx_sales_order_creation_test.main',(x_errbuf,x_retcode,cust_acc_id_v,bill_to_site_v,ship_to_site_v,inventory_item_id_v,None,None,x_ordernumber))
        
        speech = "Your order is successfully created, the order number is : "+str(x_ordernumber.getvalue()).replace(".0"," ")
    else:
        speech = "Thanks for contacting us."
    print ("Response:")
    print(speech)
    return {
    "speech": speech,
    "displayText": speech,
    "source": "Health_Care"
  }   
  
def GetName(req):
    result = req.get("result")
    parameters = result.get("parameters")
    name = parameters.get("given-name")
    #parameters.get("number")
    connection = cx_Oracle.connect('appsro/appsro@ussltcovm191.solutions.glbsnet.com:1521/VISION')
    cursor = connection.cursor()
    querystring = "select last_name from apps.per_people_f where rownum=1 and first_name='"+name+"'"
    cursor.execute(querystring)
    speech = cursor.fetchall()
    print ("Response:")
    value_intrm=str(speech[0])
    value=name+", your last name is "+value_intrm[2:-3]
    print(value)
    print (speech[0])
    return {
    "speech": value,
    "displayText": value,
    "source": "Health_Care"
  }


  

if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    print ("Starting app on port %d" %(port))
    app.run(debug=True, port=port, host='0.0.0.0')

