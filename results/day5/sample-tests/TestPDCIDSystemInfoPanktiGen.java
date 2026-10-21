package org.apache.pdfbox.pdmodel.font;
import com.thoughtworks.xstream.XStream;
import java.io.File;
import java.util.Scanner;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
public class TestPDCIDSystemInfoPanktiGen {
    static XStream xStream = new XStream();

    private <T> T deserializeObject(String serializedObjectString) {
        return (T) xStream.fromXML(serializedObjectString);
    }

    private <T> T deserializeObject(File serializedObjectFile) throws Exception {
        Scanner scanner = new Scanner(serializedObjectFile);
        String serializedObjectString = scanner.useDelimiter("\\A").next();
        return (T) xStream.fromXML(serializedObjectString);
    }

    @Test
    public void testGetRegistry1() throws Exception {
        String receivingObjectStr = 
        "<org.apache.pdfbox.pdmodel.font.PDCIDSystemInfo>" +
        "  <dictionary>" +
        "    <direct>true</direct>" +
        "    <needToBeUpdated>false</needToBeUpdated>" +
        "    <items class=\"org.apache.pdfbox.util.SmallMap\">" +
        "      <mapArr>" +
        "        <org.apache.pdfbox.cos.COSName>" +
        "          <direct>false</direct>" +
        "          <name>Registry</name>" +
        "          <hashCode>-625568675</hashCode>" +
        "        </org.apache.pdfbox.cos.COSName>" +
        "        <org.apache.pdfbox.cos.COSString>" +
        "          <direct>true</direct>" +
        "          <bytes>QWRvYmU=</bytes>" +
        "          <forceHexForm>false</forceHexForm>" +
        "        </org.apache.pdfbox.cos.COSString>" +
        "        <org.apache.pdfbox.cos.COSName>" +
        "          <direct>false</direct>" +
        "          <name>Ordering</name>" +
        "          <hashCode>1298958836</hashCode>" +
        "        </org.apache.pdfbox.cos.COSName>" +
        "        <org.apache.pdfbox.cos.COSString>" +
        "          <direct>true</direct>" +
        "          <bytes>SWRlbnRpdHk=</bytes>" +
        "          <forceHexForm>false</forceHexForm>" +
        "        </org.apache.pdfbox.cos.COSString>" +
        "        <org.apache.pdfbox.cos.COSName>" +
        "          <direct>false</direct>" +
        "          <name>Supplement</name>" +
        "          <hashCode>1281471705</hashCode>" +
        "        </org.apache.pdfbox.cos.COSName>" +
        "        <org.apache.pdfbox.cos.COSInteger>" +
        "          <direct>true</direct>" +
        "          <value>0</value>" +
        "        </org.apache.pdfbox.cos.COSInteger>" +
        "      </mapArr>" +
        "    </items>" +
        "  </dictionary>" +
        "</org.apache.pdfbox.pdmodel.font.PDCIDSystemInfo>";
        org.apache.pdfbox.pdmodel.font.PDCIDSystemInfo receivingObject = deserializeObject(receivingObjectStr);
        String returnedObjectStr = 
        "<string>Adobe</string>";
        java.lang.String expectedObject = deserializeObject(returnedObjectStr);
        Assert.assertEquals(expectedObject, receivingObject.getRegistry());
    }

    @Before
    public void setUpXStream() {
        xStream.registerConverter(new FileCleanableConverter());
        xStream.registerConverter(new InflaterConverter());
        xStream.registerConverter(new CleanerImplConverter());
    }

    @Test
    public void testGetOrdering1() throws Exception {
        String receivingObjectStr = 
        "<org.apache.pdfbox.pdmodel.font.PDCIDSystemInfo>" +
        "  <dictionary>" +
        "    <direct>true</direct>" +
        "    <needToBeUpdated>false</needToBeUpdated>" +
        "    <items class=\"org.apache.pdfbox.util.SmallMap\">" +
        "      <mapArr>" +
        "        <org.apache.pdfbox.cos.COSName>" +
        "          <direct>false</direct>" +
        "          <name>Registry</name>" +
        "          <hashCode>-625568675</hashCode>" +
        "        </org.apache.pdfbox.cos.COSName>" +
        "        <org.apache.pdfbox.cos.COSString>" +
        "          <direct>true</direct>" +
        "          <bytes>QWRvYmU=</bytes>" +
        "          <forceHexForm>false</forceHexForm>" +
        "        </org.apache.pdfbox.cos.COSString>" +
        "        <org.apache.pdfbox.cos.COSName>" +
        "          <direct>false</direct>" +
        "          <name>Ordering</name>" +
        "          <hashCode>1298958836</hashCode>" +
        "        </org.apache.pdfbox.cos.COSName>" +
        "        <org.apache.pdfbox.cos.COSString>" +
        "          <direct>true</direct>" +
        "          <bytes>SWRlbnRpdHk=</bytes>" +
        "          <forceHexForm>false</forceHexForm>" +
        "        </org.apache.pdfbox.cos.COSString>" +
        "        <org.apache.pdfbox.cos.COSName>" +
        "          <direct>false</direct>" +
        "          <name>Supplement</name>" +
        "          <hashCode>1281471705</hashCode>" +
        "        </org.apache.pdfbox.cos.COSName>" +
        "        <org.apache.pdfbox.cos.COSInteger>" +
        "          <direct>true</direct>" +
        "          <value>0</value>" +
        "        </org.apache.pdfbox.cos.COSInteger>" +
        "      </mapArr>" +
        "    </items>" +
        "  </dictionary>" +
        "</org.apache.pdfbox.pdmodel.font.PDCIDSystemInfo>";
        org.apache.pdfbox.pdmodel.font.PDCIDSystemInfo receivingObject = deserializeObject(receivingObjectStr);
        String returnedObjectStr = 
        "<string>Identity</string>";
        java.lang.String expectedObject = deserializeObject(returnedObjectStr);
        Assert.assertEquals(expectedObject, receivingObject.getOrdering());
    }
}