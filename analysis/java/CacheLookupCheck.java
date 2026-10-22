import com.thoughtworks.xstream.XStream;
import com.thoughtworks.xstream.security.AnyTypePermission;
import java.io.File;
import java.lang.ref.SoftReference;
import java.lang.reflect.Field;
import java.util.Map;
import org.apache.pdfbox.cos.COSObject;
import org.apache.pdfbox.pdmodel.DefaultResourceCache;

/**
 * Why a generated test of DefaultResourceCache.get*(COSObject) fails with "expected:<...> but was:<null>"
 * (docs/failure-analysis.md). Deserialises the receiving object and the parameter of one test exactly as the test
 * does (XStream), then reports:
 *   - how many entries the deserialised cache holds, and how many still reference an object (SoftReference.get());
 *   - whether the deserialised parameter is one of the cache's keys (the map compares COSObject by identity);
 *   - the result of the call with the deserialised parameter, and with the cache key that has the same object
 *     number.
 *
 * Usage: java -cp <pdfbox, fontbox, commons-logging, xstream 1.4.12 and its dependencies> CacheLookupCheck.java
 *            <method: getFont | getColorSpace | getXObject | getExtGState> <receiving.xml> <params.xml>
 */
public class CacheLookupCheck {
    public static void main(String[] args) throws Exception {
        String method = args[0];
        XStream xStream = new XStream();
        xStream.addPermission(AnyTypePermission.ANY);
        DefaultResourceCache cache = (DefaultResourceCache) xStream.fromXML(new File(args[1]));
        Object[] params = (Object[]) xStream.fromXML(new File(args[2]));
        COSObject param = (COSObject) params[0];

        String fieldName = method.equals("getFont") ? "fonts" : method.equals("getColorSpace") ? "colorSpaces"
                : method.equals("getXObject") ? "xobjects" : "extGStates";
        Field field = DefaultResourceCache.class.getDeclaredField(fieldName);
        field.setAccessible(true);
        Map<?, ?> map = (Map<?, ?>) field.get(cache);
        int referenced = 0;
        COSObject sameNumber = null;
        for (Map.Entry<?, ?> e : map.entrySet()) {
            if (((SoftReference<?>) e.getValue()).get() != null) {
                referenced++;
            }
            COSObject key = (COSObject) e.getKey();
            if (key.getObjectNumber() == param.getObjectNumber()
                    && key.getGenerationNumber() == param.getGenerationNumber()) {
                sameNumber = key;
            }
        }
        java.lang.reflect.Method m = DefaultResourceCache.class.getMethod(method, COSObject.class);
        System.out.println("method: " + method);
        System.out.println("cache entries: " + map.size() + ", still referencing an object: " + referenced);
        System.out.println("parameter: object " + param.getObjectNumber() + " " + param.getGenerationNumber()
                + "; parameter is a key of the cache (identity): " + map.containsKey(param));
        System.out.println("call with the deserialised parameter: " + m.invoke(cache, param));
        System.out.println("cache key with the same object number: " + (sameNumber != null));
        if (sameNumber != null) {
            System.out.println("call with that key: " + m.invoke(cache, sameNumber));
        }
    }
}
