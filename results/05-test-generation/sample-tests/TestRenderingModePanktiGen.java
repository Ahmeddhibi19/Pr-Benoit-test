package org.apache.pdfbox.pdmodel.graphics.state;
import com.thoughtworks.xstream.XStream;
import java.io.File;
import java.util.Scanner;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
public class TestRenderingModePanktiGen {
    static XStream xStream = new XStream();

    private <T> T deserializeObject(String serializedObjectString) {
        return (T) xStream.fromXML(serializedObjectString);
    }

    private <T> T deserializeObject(File serializedObjectFile) throws Exception {
        Scanner scanner = new Scanner(serializedObjectFile);
        String serializedObjectString = scanner.useDelimiter("\\A").next();
        return (T) xStream.fromXML(serializedObjectString);
    }

    @Before
    public void setUpXStream() {
        xStream.registerConverter(new FileCleanableConverter());
        xStream.registerConverter(new InflaterConverter());
        xStream.registerConverter(new CleanerImplConverter());
    }

    @Test
    public void testIsFill1() throws Exception {
        String receivingObjectStr = 
        "<org.apache.pdfbox.pdmodel.graphics.state.RenderingMode>FILL</org.apache.pdfbox.pdmodel.graphics.state.RenderingMode>";
        org.apache.pdfbox.pdmodel.graphics.state.RenderingMode receivingObject = deserializeObject(receivingObjectStr);
        Assert.assertEquals(true, receivingObject.isFill());
    }
}