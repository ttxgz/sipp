import csv
import copy
from os import path

from xml.etree.ElementTree import parse, Element, Comment
from xml.etree import ElementTree

TEMPLATE_DIR = 'template'
EMPTY_TF = 'empty.xml'
INVITE_TMPT = 'invite.xml'
TMPT = 'template.xml'

def AppendTag(ele, output):
	for child in ele:
		output.append(child)

def FindParam(params, inputs, param, default_val):
	if (len(inputs) < params.index(param) + 1):
		return default_val
	else:
		return inputs[params.index(param)]

def AppendComment(ele, txt):
	cmt = Comment(txt)
	cmt.tail = '\n'
	ele.append(cmt)

def MakeCDATA(ele):
	cdata_str = ele.text.split('\n', 1)[1].replace('\n', '<![CDATA[', 1) + ']]>'
	cdata = Comment(' Generated CDATA -->\n' + cdata_str + '\n<!-- End of Generated CDATA ')
	cdata.tail = '\n'
	ele.append(cdata)
	ele.text = ''

def MakeCDATAAll(tree):
	for send in tree.findall('send'):
		MakeCDATA(send)

def GenCreateConf(create_conf_msg, create_conf_tmplt, output_root):
	params = ['cmd', 'conf_id','ri']
	conf_id = FindParam(params, create_conf_msg, 'conf_id', 'conf_0')
	nop = create_conf_tmplt.find('nop')
	nop.attrib['display'] = nop.attrib['display'].replace('[conf_id]', conf_id)
	ri = FindParam(params, create_conf_msg, 'ri', '3s')
	send = create_conf_tmplt.find('send')
	send.text = send.text.replace('[conf_id]', conf_id)
	send.text = send.text.replace('[ri]', ri)
	MakeCDATA(send)
	AppendTag(create_conf_tmplt, output_root)

def GenRecording(record_msg, record_tmplt, output_root):
	params = ['cmd', 'record_dur', 'format', 'record_file']
	record_dur = FindParam(params, record_msg, 'record_dur', '3s')
	record_format = FindParam(params, record_msg, 'format', 'dvcr')
	record_file = FindParam(params, record_msg, 'record_file', 'file://transient/[$client_sip_id]_placeholder.wav')
	nop = record_tmplt.find('nop')
	nop.attrib['display'] = nop.attrib['display'].replace('[record_dur]', record_dur)
	for send in record_tmplt.findall('send'):
		send.text = send.text.replace('[record_dur]', record_dur)
		send.text = send.text.replace('[record_format]', record_format)
		send.text = send.text.replace('[record_file]', record_file)
		MakeCDATA(send)
	AppendTag(record_tmplt, output_root)

def GenPlayback(playback_msg, playback_tmplt, output_root):
	params = ['cmd', 'target','wav_file']
	target = FindParam(params, playback_msg, 'target', 'conf:conf_0')
	wav_file = FindParam(params, playback_msg, 'wav_file', 'file://transient/[$client_sip_id]_placeholder.wav')
	nop = playback_tmplt.find('nop')
	nop.attrib['display'] = nop.attrib['display'].replace('[target]', target)
	nop.attrib['display'] = nop.attrib['display'].replace('[wav_file]', wav_file)
	for send in playback_tmplt.findall('send'):
		send.text = send.text.replace('[target]', target)
		send.text = send.text.replace('[wav_file]', wav_file)
		MakeCDATA(send)
	AppendTag(playback_tmplt, output_root)

def GenJoinConf(join_conf_msg, join_conf_tmplt, output_root):
	params = ['cmd', 'conf_id']
	conf_id = FindParam(params, join_conf_msg, 'conf_id', 'conf_0')
	nop = join_conf_tmplt.find('nop')
	nop.attrib['display'] = nop.attrib['display'].replace('[conf_id]', conf_id)
	send = join_conf_tmplt.find('send')
	send.text = send.text.replace('[conf_id]', conf_id)
	MakeCDATA(send)
	AppendTag(join_conf_tmplt, output_root)

def GenWait(wait_msg, wait_tmplt, output_root):
	params = ['cmd', 'wait_dur']
	wait_dur = FindParam(params, wait_msg, 'wait_dur', '3000')
	nop = wait_tmplt.find('nop')
	nop.attrib['display'] = nop.attrib['display'].replace('[wait_dur]', wait_dur)
	pause = wait_tmplt.find('pause')
	pause.attrib['milliseconds'] = wait_dur
	AppendTag(wait_tmplt, output_root)

def GenPLAY(play_msg, play_tmplt, output_root):
	params = ['cmd', 'wav_file', 'format', 'repeat']
	wav_file = FindParam(params, play_msg, 'wav_file', 'UnknownWav')
	nop = play_tmplt.find('nop')
	nop.attrib['display'] = nop.attrib['display'].replace('[wav_file]', wav_file)
	# play format
	format = FindParam(params, play_msg, 'format', 'PCMA')
	if (format == 'PCMU'):
		format = 0
	elif (format == 'PCMA'):
		format = 8
	elif (play_msg[2] == 'G729'):
		format = 18
	repeat = FindParam(params, play_msg, 'repeat', -1) # default: loop over
	exec = play_tmplt.find('nop/action/exec')
	exec.attrib['rtp_stream'] = wav_file + ', ' + str(repeat) + ', ' + str(format)
	AppendTag(play_tmplt, output_root)

def GenINVITE(inv_msg, inv_tmplt, output_root, sdp_less = False):
	params = ['cmd','audio_format','log_id','uri_user']
	# set sdp
	sdp_media_id = []
	sdp_media_map = []
	audio_format = FindParam(params, inv_msg,'audio_format','PCMA')
	if (audio_format == 'PCMU'):
		sdp_media_id.append('0')
		sdp_media_map.append('a=rtpmap:0 PCMU/8000')
	# default: PCMA
	else:
		sdp_media_id.append('8')
		sdp_media.append('a=rtpmap:8 PCMA/8000\n')

	sdp_m = inv_tmplt.find("nop/action/assignstr[@assign_to='sdp_m']")
	sdp_m.attrib['value'] = ' '.join(sdp_media_id)
	sdp_a = inv_tmplt.find("nop/action/assignstr[@assign_to='sdp_a']")
	sdp_a.attrib['value'] = '\n'.join(sdp_media_map)
	#set sdp to Invite or to Ack for sdp_less
	if (sdp_less):
		sdp_ack = inv_tmplt.find("nop/action/assignstr[@assign_to='sdp_ack']")
		sdp_ack.attrib['value'] = "[$sdp]"
	else:
		sdp_invite = inv_tmplt.find("nop/action/assignstr[@assign_to='sdp_invite']")
		sdp_invite.attrib['value'] = "[$sdp]"

	#set uri_user
	uri_user = FindParam(params, inv_msg, 'uri_user','sipp')
	send_invite = inv_tmplt.find("send")
	send_invite.text = send_invite.text.replace('[uri_user]', uri_user)

	#set log_id
	log_id = FindParam(params, inv_msg, 'log_id','sipp_client')
	send_invite.text = send_invite.text.replace('[log_id]', log_id)

	MakeCDATAAll(inv_tmplt)

	AppendTag(inv_tmplt, output_root)

def GenINVITEConfLeg(inv_leg_msg, inv_leg_tmplt, output_root):
	params = ['cmd','log_id']
	sends = inv_leg_tmplt.findall('send')
	send_invite = sends[0]
	log_id = FindParam(params, inv_leg_msg,'log_id','sipp_conf')
	send_invite.text = send_invite.text.replace('[log_id]', log_id)

	# Convert CDATA in all sends
	MakeCDATAAll(inv_leg_tmplt)

	AppendTag(inv_leg_tmplt, output_root)

def GenBye(bye_msg, bye_tmplt, output_root):
	params = ['cmd']
	MakeCDATAAll(bye_tmplt)
	AppendTag(bye_tmplt, output_root)

def GenReInviteOrINFO(reinv_or_info_msg, reinv_or_info_tmplt, output_root):
	params = ['cmd','loop_out_cnt']
	# set loop out cnt
	loop_cnt = int(FindParam(params, reinv_or_info_msg,'loop_out_cnt','0'))
	if loop_cnt > 0:
		loop_max = reinv_or_info_tmplt.find("nop/action/assign[@assign_to='reinvite_loop_max']")
		loop_max.attrib['value'] = str(loop_cnt)
		loop_increment = reinv_or_info_tmplt.find("nop/action/assign[@assign_to='reinvite_loop_increment']")
		loop_increment.attrib['value'] = '1'

	MakeCDATAAll(reinv_or_info_tmplt)
	AppendTag(reinv_or_info_tmplt, output_root)

def InsertXMLTag(sipp_msg, tmplt_root, output_root):
	if (sipp_msg[0] == 'INVITE'):
		GenINVITE(sipp_msg, copy.deepcopy(tmplt_root.find('invite')), output_root)
	elif (sipp_msg[0] == 'INVITE_SDPLESS'):
		GenINVITE(sipp_msg, copy.deepcopy(tmplt_root.find('invite')), output_root, True)
	elif (sipp_msg[0] == 'INVITE_CONF'):
		GenINVITEConfLeg(sipp_msg, copy.deepcopy(tmplt_root.find('invite_conf_leg')), output_root)
	elif (sipp_msg[0] == 'PLAY'):
		GenPLAY(sipp_msg, copy.deepcopy(tmplt_root.find('play')), output_root)
	elif (sipp_msg[0] == 'CREATE_CONF'):
		GenCreateConf(sipp_msg, copy.deepcopy(tmplt_root.find('create_conf')), output_root)
	elif (sipp_msg[0] == 'JOIN_CONF'):
		GenJoinConf(sipp_msg, copy.deepcopy(tmplt_root.find('join_conf')), output_root)
	elif (sipp_msg[0] == 'RECORDING'):
		GenRecording(sipp_msg, copy.deepcopy(tmplt_root.find('recording')), output_root)
	elif (sipp_msg[0] == 'PLAYBACK'):
		GenPlayback(sipp_msg, copy.deepcopy(tmplt_root.find('playback')), output_root)
	elif (sipp_msg[0] == 'WAIT'):
		GenWait(sipp_msg, copy.deepcopy(tmplt_root.find('wait')), output_root)
	elif (sipp_msg[0] == 'BYE'):
		GenBye(sipp_msg, copy.deepcopy(tmplt_root.find('bye')), output_root)
	elif (sipp_msg[0] == 'INFO_OR_REINVITE'):
		GenReInviteOrINFO(sipp_msg, copy.deepcopy(tmplt_root.find('reInvite_or_INFO')), output_root)
	else:
		print("Oops, not support " + sipp_msg[0] + " yet!")

def	GenerateXML(sipp_msg_list, output_file):
	# open and create an initial xml doc
	output_doc = parse(path.join(TEMPLATE_DIR, EMPTY_TF))
	output_root = output_doc.getroot()
	tmplt_root = parse(path.join(TEMPLATE_DIR, TMPT)).getroot()
	# iterate every sipp msg and generate xml
	for sipp_msg in sipp_msg_list:
		InsertXMLTag(sipp_msg, tmplt_root, output_root)
	# write xml to output file
	output_doc.write(output_file, 'ISO-8859-1', xml_declaration = True)
	return True;

