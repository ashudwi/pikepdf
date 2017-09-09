import pytest
from pikepdf import _qpdf as qpdf

import os
import platform
import shutil
from contextlib import suppress


def test_create_form_xobjects(outdir):
    pdf = qpdf.Pdf.new()

    font = pdf.make_indirect(
        qpdf.Object.parse(b"""
            <<
                /Type /Font
                /Subtype /Type1
                /Name /F1
                /BaseFont /Helvetica
                /Encoding /WinAnsiEncoding
            >>"""))

    width, height = 100, 100
    image_data = b"\xff\x7f\x00" * (width * height)

    image = qpdf.Object.Stream(pdf, image_data)
    image.stream_dict = qpdf.Object.parse("""
            <<
                /Type /XObject
                /Subtype /Image
                /ColorSpace /DeviceRGB
                /BitsPerComponent 8
                /Width 100
                /Height 100
            >>""")
    xobj_image = qpdf.Object.Dictionary({'/Im1': image})

    form_xobj_res = qpdf.Object.Dictionary({
        '/XObject': xobj_image
        })
    form_xobj = qpdf.Object.Stream(pdf, b"""
        /Im1 Do
        """)
    form_xobj['/Type'] = qpdf.Object.Name('/XObject')
    form_xobj['/Subtype'] = qpdf.Object.Name('/Form')
    form_xobj['/FormType'] = 1
    form_xobj['/Matrix'] = [1, 0, 0, 1, 0, 0]
    form_xobj['/BBox'] = [0, 0, 1, 1]
    print(form_xobj_res.owner)
    form_xobj['/Resources'] = form_xobj_res


    rfont = {'/F1': font}

    resources = {
        '/Font': rfont,
        '/XObject': {'/Form1': form_xobj},
        }

    mediabox = [0, 0, 612, 792]

    stream = b"""
        BT /F1 24 Tf 72 720 Td (Hi there) Tj ET
        q 144 0 0 144 234 324 cm /Form1 Do Q
        q 72 0 0 72 378 180 cm /Form1 Do Q
        """

    contents = qpdf.Object.Stream(pdf, stream)

    page = pdf.make_indirect({
        '/Type': qpdf.Object.Name('/Page'),
        '/MediaBox': mediabox,
        '/Contents': contents,
        '/Resources': resources
        })

    pdf.add_page(page, True)
    pdf.save(outdir / 'formxobj.pdf')
