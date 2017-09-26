import csv
from os import path

from xml.etree.ElementTree import parse, Element, Comment
from xml.etree import ElementTree

TEMPLATE_DIR = 'template'
EMPTY_TF = 'empty.xml'
INVITE_TMPT = 'invite.xml'

#def CDATA(text=None):
#    element = etree.Element(CDATA)
#    element.text = text
#    return element

#class ElementTreeCDATA(etree.ElementTree):
#    def _write(self, file, node, encoding, namespaces):
#        if node.tag is CDATA:
#            text = node.text.encode(encoding)
#            file.write("\n<![CDATA[%s]]>\n" % text)
#        else:
#            etree.ElementTree._write(self, file, node, encoding, namespaces)

def MakeCDATA(text):
	return Comment(' Generated CDATA -->\n' + text.replace('\n', '<![CDATA[', 1) + ']]>\n<!-- End of Generated CDATA ')

def GenINVITE(inv_msg, output_root):
	tmplt_file = path.join(TEMPLATE_DIR, INVITE_TMPT)
	doc = parse(tmplt_file)
	root = doc.getroot()
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

	send = root.find('send')
	send_cdata = send.text
	send_cdata = send_cdata.replace('[sdp_m]', sdp_m)
	send_cdata = send_cdata.replace('[sdp_media]', '\n'.join(sdp_media))

	#send.text = CDATA(send.text)
	#send.append(Comment(' Generated CDATA -->\n<![CDATA[' + send_cdata.replace(']]>', ']]]]><![CDATA[>') + ']]>\n<!-- End of Generated CDATA '))
	send.append(MakeCDATA(send_cdata))
	send.text = ''
	#send.append(send_cdata)
	#send.text = ''
	#send.text = MakeCDATA(send.text)
	output_root.append(root)
	return

def InsertXMLTag(sipp_msg, output_root):
	#cmt = Comment(''.join(sipp_msg))
	#root.append(cmt)
	if (sipp_msg[0] == 'INVITE'):
		GenINVITE(sipp_msg, output_root)
	return

def	GenerateXML(sipp_msg_list, output_file):
	# open and create an initial xml doc
	output_doc = parse(path.join(TEMPLATE_DIR, EMPTY_TF))
	output_root = output_doc.getroot()
	# iterate every sipp msg and generate xml
	for sipp_msg in sipp_msg_list:
		InsertXMLTag(sipp_msg, output_root)
	# write xml to output file
	output_doc.write('output.xml')
	return True;

