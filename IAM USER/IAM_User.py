#Author: Sumitha Rao
#CreatedOn: 30/12/2019
#UpdatedOn: 30/12/2019
#Version: V1
#Description: Create a simple IAM role
#Product: Cloud Exponence

import boto3,sys,json
def stack_exists(inputStack):
    cfn_rs = boto3.resource('cloudformation')
    return [True for stack in cfn_rs.stacks.all() if (stack.name)==(inputStack)]
def iam_user_creation(event,StackURL):
    
    #Mandatory Inputs and Parameter
    mandatoryInputs = ['Region','StackName','Tags','UserName','Password']
    #Optional Parameters
    optionalCftParameters = ['GroupName','PolicyArn','Path','ManagedPolicyArns','PasswordResetRequired','PermissionsBoundary']

    #1. Assign and Validate Inputs
    try:
        #Mandatory inputs. If missed, will throw error
        eventKeys = event.keys()
        region = event['Region']
        stackName = event['StackName']      
        cftTags = event['Tags']
        cftParameters = []
        cftParameters.append( {'ParameterKey': 'UserName','ParameterValue': event['UserName']})
        cftParameters.append( {'ParameterKey': 'Password','ParameterValue': event['Password']})        
        #Validating Optional Parameters
        receivedOptionalParameters = list( set( optionalCftParameters ) & set( eventKeys ) )
        for param in receivedOptionalParameters:
            cftParameters.append( {'ParameterKey': param,'ParameterValue': event[param]})
    except Exception as e:
        message = "Missing Input Values. Need value for " + str(e)
        #remove the quotes in the error message
        message = message.replace("'",' ') 
        message = message.replace('"',' ')
        return {
            "Status" : "FAILED",
            "Status_Reason" : message
        }

    #2. Create CFT Stack
    try:
        cloudFormation = boto3.resource('cloudformation',region_name=region)
        if stack_exists(stackName):	 
           responseCFT=boto3.client('cloudformation').update_stack(
             StackName=stackName, 
             TemplateURL=StackURL,
             Capabilities=[
             'CAPABILITY_NAMED_IAM',
             ],
             Parameters=cftParameters,
             Tags= cftTags                
        )
        else:           
            responseCFT = cloudFormation.create_stack(
              StackName=stackName,
              TemplateURL= StackURL,
              Parameters= cftParameters,
              Capabilities=[
              'CAPABILITY_NAMED_IAM',
              ],
              Tags= cftTags
            )
    except Exception as e:
        message = "Failed to initiate creation of IAM.\nError Message: " + str(e)
        #remove the quotes in the error message
        message = message.replace("'",' ') 
        message = message.replace('"',' ')
        return {
            "Status" : "FAILED",
            "Status_Reason" : message
        }

    #3. Check Initial Status
    try:
        responseSN = {}
        checkstack = boto3.client('cloudformation',region_name=region)
        responsecftcheck=checkstack.describe_stacks(StackName= stackName)
        if responsecftcheck['Stacks'][0]['StackStatus'] == 'CREATE_IN_PROGRESS' or responsecftcheck['Stacks'][0]['StackStatus']=='UPDATE_IN_PROGRESS':
            responseSN['Status_Code']=200
            responseSN['Status']='SUCCESS'
            responseSN['Status_Reason']='IAM User Creation/Updation is Initiated.'
        elif responsecftcheck['Stacks'][0]['StackStatus'] == 'CREATE_FAILED' or responsecftcheck['Stacks'][0]['StackStatus'] == 'UPDATE_FAILED':
            responseSN['Status']='FAILED'
            responseSN['Status_Reason']= responsecftcheck['Stacks'][0]['StackStatusReason']
        return responseSN
    except Exception as e:
        message = "Failed to get initial status of IAM User Creation Stack. \n Error Message: " + str(e)
        #remove the quotes in the error message
        message = message.replace("'",' ') 
        message = message.replace('"',' ')
        return {
            "Status" : "FAILED",
            "Status_Reason" : message
        }

event = json.loads(sys.argv[1]) 
StackURL = sys.argv[2]
print( iam_user_creation( event , StackURL ) )
