import csv
from os import path

from xml.etree.ElementTree import parse, Element, Comment
from xml.etree import ElementTree

TEMPLATE_DIR = 'template'
EMPTY_TF = 'empty.xml'
INVITE_TMPT = 'invite.xml'
TMPT = 'template.xml'

def AppendComment(ele, txt):
	cmt = Comment(txt)
	cmt.tail = '\n'
	ele.append(cmt)
	return

def MakeCDATA(ele):
	cdata_str = ele.text.split('\n', 1)[1].replace('\n', '<![CDATA[', 1) + ']]>'
	cdata = Comment(' Generated CDATA -->\n' + cdata_str + '\n<!-- End of Generated CDATA ')
	cdata.tail = '\n'
	ele.append(cdata)
	ele.text = ''

def GenINVITE(inv_msg, inv_tmplt, output_root):
	#tmplt_file = path.join(TEMPLATE_DIR, INVITE_TMPT)
	#doc = parse(tmplt_file)
	#root = doc.getroot()
	sends = inv_tmplt.findall('send')
	send_sdp = sends[0]
	# TODO: improve to a helper func to construct INVITE SDP
	sdp_m = ''
	sdp_media = []
	if (len(inv_msg) >= 2):
		if (inv_msg[1] == 'PCMU'):
			sdp_m = 'm=audio [media_port] RTP/AVP 0'
			sdp_media.append('a=rtpmap:0 PCMU/8000')
	else:
		sdp_m = 'm=audio [media_port] RTP/AVP 8\n'
		sdp_media.append('a=rtpmap:8 PCMA/8000\n')

	send_sdp.text = send_sdp.text.replace('[sdp_m]', sdp_m)
	send_sdp.text = send_sdp.text.replace('[sdp_media]', '\n'.join(sdp_media))
	MakeCDATA(send_sdp)

	# Convert CDATA in ACK
	MakeCDATA(sends[1])

	for child in inv_tmplt:
		output_root.append(child)
		output_root.append(test_cmt)
	return

def InsertXMLTag(sipp_msg, tmplt_root, output_root):
	if (sipp_msg[0] == 'INVITE'):
		GenINVITE(sipp_msg, tmplt_root.find('invite'), output_root)
	return

def	GenerateXML(sipp_msg_list, output_file):
	# open and create an initial xml doc
	output_doc = parse(path.join(TEMPLATE_DIR, EMPTY_TF))
	output_root = output_doc.getroot()
	tmplt_root = parse(path.join(TEMPLATE_DIR, TMPT)).getroot()
	# iterate every sipp msg and generate xml
	for sipp_msg in sipp_msg_list:
		InsertXMLTag(sipp_msg, tmplt_root, output_root)
	# write xml to output file
	output_doc.write('output.xml', 'ISO-8859-1', xml_declaration = True)
	return True;

