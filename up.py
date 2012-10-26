#!/usr/bin/python

from boto import ec2
from boto.exception import EC2ResponseError
from ansible import errors
from ansible import callbacks
from ansible import utils
import ansible
import ansible.playbook
import sys
import os
import time
import json

c = ec2.EC2Connection()

# centos 6.3 box
IMG='ami-13e1c456'
MIN=1
MAX=1
TYPE='t1.micro'


KEY_NAME='nx_box'
print "Creating KeyPair", KEY_NAME
try:
    KEY = c.create_key_pair(KEY_NAME)
    KEY.save("~/.ssh")
except EC2ResponseError as e:
    if e.error_code == "InvalidKeyPair.Duplicate":
        sys.stderr.write( "Duplicate KeyPair... attempting to continue\n" )
    else:
        sys.stderr.write( "EC2ResponseError on create_key_pair\n" )
        sys.stderr.write( "Error code: " + e.error_code + "\n" )
        sys.stderr.write( "Status: " + str(e.status) + "\n" )
        sys.stderr.write( "Error Message: " + e.error_message + "\n" )
        sys.stderr.write( "Error Reason: " + e.reason + "\n" )
        sys.stderr.write( "Exiting... \n" )
        exit(-1)

SEC_NAME = 'nxGrp'
print "Creating Security Group", SEC_NAME
SEC_DESC = 'ssh -p 22'
try:
    mGrp = c.create_security_group(SEC_NAME,SEC_DESC)
    mGrp.authorize('tcp',22,22,'0.0.0.0/0')
except EC2ResponseError as e:
    if e.error_code == "InvalidGroup.Duplicate":
        sys.stderr.write( "Duplicate Security Group... attempting to continue\n" )
    else:
        sys.stderr.write( "EC2ResponseError on create_security_group\n" )
        sys.stderr.write( "Error code: " + e.error_code + "\n" )
        sys.stderr.write( "Status: " + str(e.status) + "\n" )
        sys.stderr.write( "Error Message: " + e.error_message + "\n" )
        sys.stderr.write( "Error Reason: " + e.reason + "\n" )
        sys.stderr.write( "Exiting... \n" )
        exit(-1)

# change to (KEY=VALUE,...) format
SEC_NAMES = [SEC_NAME]
r = c.run_instances(IMG,MIN,MAX,KEY_NAME,SEC_NAMES,None,None,TYPE)
i = r.instances[0]
print "Launching the instance: ", i.id 
f=open('./instance_id','w+')
f.write(time.strftime('%Y%m%d%H%M%S'))
f.write(": Made instance with id: " + str(i.id))
f.close()

time.sleep(2) # Sleep to prevent i.update error, instances does not exist
print "Waiting for the instance to get a public_dns_name..."
while i.public_dns_name is "":
    i.update()

print "Hello! I am instance: " + i.id + " and my public dns name is: " + i.public_dns_name

#os.environ["ANSIBLE_HOSTS"] = './ansible_hosts'
f=open('./ansible_hosts','w')
f.write(str(i.public_dns_name))
f.close()

# while public DNS name null, i.update, i.public_dns_name
# write public DNS to ansible_hosts
# os.environ["ANSIBLE_HOSTS"] = i.public_dns_name
# runner = ansible.runner.Runner(
# remote_user="ec2-user",
# host_list=os.path.expanduser('~/ansible_hosts'),
# module_name='ping',
# module_args='',
# pattern='*'
# )
# datastructure = runner.run()

# print json.dumps(datastructure,indent=4)

# TODO: while SSH attempt fails, sleep, retry

print "Sleeping 60s, waiting for instance to start sshd"
time.sleep(60)

stats = callbacks.AggregateStats()
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

# Runner run playbook?
nx_play = ansible.playbook.PlayBook(
   remote_user="ec2-user",
   host_list=os.path.expanduser('./ansible_hosts'),
   stats=stats,
   callbacks=playbook_cb,
   runner_callbacks=runner_cb,
   sudo=True,
   private_key_file=os.path.expanduser('~/.ssh/'+KEY_NAME+".pem"),
   playbook=os.path.expanduser('./up.yml')
)

data = nx_play.run()
print json.dumps(data,indent=4)

#         FROM DEHAAANNNNNN
#        stats = callbacks.AggregateStats()
#        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
#        runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

#        pb = ansible.playbook.PlayBook(
#            playbook=playbook,
#            module_path=options.module_path,
#            host_list=options.inventory,
#            forks=options.forks,
#            remote_user=options.remote_user,
#            remote_pass=sshpass,
#            callbacks=playbook_cb,
#            runner_callbacks=runner_cb,
#            stats=stats,
#            timeout=options.timeout,
#            transport=options.connection,
#            sudo=options.sudo,
#            sudo_user=options.sudo_user,
#            sudo_pass=sudopass,
#            extra_vars=extra_vars,
#            private_key_file=options.private_key_file,
#            only_tags=only_tags,
#            subset=options.subset,
#        )


