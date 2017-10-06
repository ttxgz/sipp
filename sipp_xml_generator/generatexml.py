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

def GenINVITE(inv_msg, inv_tmplt, output_root):
	params = ['cmd','audio_format','uri_user']
	sends = inv_tmplt.findall('send')
	send_sdp = sends[0]
	# TODO: improve to a helper func to construct INVITE SDP
	sdp_m = ''
	sdp_media = []
	sdp_m = FindParam(params, inv_tmplt,'audio_format','PCMA')
	if (sdp_m == 'PCMU'):
		sdp_m = 'm=audio [media_port] RTP/AVP 0'
		sdp_media.append('a=rtpmap:0 PCMU/8000')
	else:
		sdp_m = 'm=audio [media_port] RTP/AVP 8\n'
		sdp_media.append('a=rtpmap:8 PCMA/8000\n')

	send_sdp.text = send_sdp.text.replace('[sdp_m]', sdp_m)
	send_sdp.text = send_sdp.text.replace('[sdp_media]', '\n'.join(sdp_media))

	uri_user = FindParam(params, inv_msg, 'uri_user','sipp')
	send_sdp.text = send_sdp.text.replace('[uri_user]', uri_user)

	MakeCDATA(send_sdp)

	# Convert CDATA in ACK
	MakeCDATA(sends[1])

	AppendTag(inv_tmplt, output_root)

def GenBye(bye_msg, bye_tmplt, output_root):
	params = ['cmd']
	send = bye_tmplt.find('send')
	MakeCDATA(send)
	AppendTag(bye_tmplt, output_root)

def InsertXMLTag(sipp_msg, tmplt_root, output_root):
	if (sipp_msg[0] == 'INVITE'):
		GenINVITE(sipp_msg, copy.deepcopy(tmplt_root.find('invite')), output_root)
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

