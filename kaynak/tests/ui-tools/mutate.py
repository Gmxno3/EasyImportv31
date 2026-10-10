import subprocess, re
import os
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.join(HERE,'..','..','roblox-studio-plugin')
core=open(os.path.join(ROOT,'UIToolsCore.lua'),encoding='utf-8').read()
plug=open(os.path.join(ROOT,'UIToolsPlugin.lua'),encoding='utf-8').read()
M=[
 ("core: sağ hizalama yanlış", 'core', 'x = c.x + c.w - r.w', 'x = c.x + c.w'),
 ("core: ızgara yukarı yuvarlama yerine tavan", 'core', 'return math.floor(v / step + 0.5) * step', 'return math.ceil(v / step) * step'),
 ("core: dikey orta yanlış", 'core', 'y = c.y + (c.h - r.h) / 2', 'y = c.y'),
 ("core: sınıf planı metni kayıp saymıyor", 'core', 'if dropSet.Text then plan.warnings[#plan.warnings + 1] = "metin silinecek" end', ''),
 ("plugin: sınıf değişiminde çocuklar taşınmıyor", 'plug', 'for _, c in ipairs(o:GetChildren()) do c.Parent = n end', ''),
 ("plugin: geri alma waypoint'i yok", 'plug', 'ChangeHistoryService:SetWaypoint("UI Tools: " .. name)', ''),
 ("plugin: öznitelik kopyalanmıyor", 'plug', 'for k, v in pairs(o:GetAttributes()) do n:SetAttribute(k, v) end', ''),
 ("plugin: Scale dönüşümü konumu bozuyor", 'plug', 'o.Position = UDim2.new(Core.toScale(px_, pw), 0, Core.toScale(py_, ph), 0)', 'o.Position = UDim2.new(Core.toScale(px_, pw), 0, 0, 0)'),
 ("plugin: layout koruması kaldırıldı", 'plug', 'if layoutControlled(o) or pw <= 0 or ph <= 0 then', 'if pw <= 0 or ph <= 0 then'),

 ("core: kaydırıcı adım yuvarlaması yok", 'core', 'raw = min + math.floor((raw - min) / step + 0.5) * step', 'raw = raw'),
 ("plugin: öznitelik temizleme çalışmıyor", 'plug', 'o:SetAttribute(k, nil)', ''),
 ("plugin: etiket temizleme çalışmıyor", 'plug', 'CollectionService:RemoveTag(o, tag)', ''),
 ("plugin: bırakınca sürükleme bitmiyor (input.Changed)", 'plug', 'if input.UserInputState == Enum.UserInputState.End then stopDrag() end', ''),
 ("plugin: fare konumu pencereye göre değil (eski hata)", 'plug', 'widget:GetRelativeMousePosition()', 'UserInputService:GetMouseLocation()'),
 ("plugin: tutamaç 0..1 dışına taşabiliyor", 'plug', 'knob.Position = UDim2.new(frac, 0, 0.5, 0)', 'knob.Position = UDim2.new(frac * 3 - 1, 0, 0.5, 0)'),
 ("plugin: Convert düğmesi eflatun değil", 'plug', 'if style == "primary" then bg = COL.lilac elseif', 'if style == "primary" then bg = COL.row elseif'),
 ("plugin: sınıf ikonu atanmıyor", 'plug', 'img.Image = d.Image', ''),
 ("core: dağıtma boşluk formülü eski hata (uç boyutları düşülmüyor)", 'core', 'for k = 1, n do total = total + rects[order[k]][size] end', 'for k = 2, n - 1 do total = total + rects[order[k]][size] end'),
 ("plugin: ok tuşu pencere odağı kontrolü kaldırıldı", 'plug', 'if gameProcessed or not windowFocused or not widget.Enabled then return end', 'if gameProcessed or not widget.Enabled then return end'),
 ("plugin: ok tuşu metin kutusu kontrolü kaldırıldı", 'plug', 'if typing then return end', ''),
 ("plugin: yerleşim çift eklenir (mevcut kontrol kaldırıldı)", 'plug', 'local c = o:FindFirstChildOfClass(class)\n\tif not c then\n\t\tc = Instance.new(class)', 'local c = nil\n\tif not c then\n\t\tc = Instance.new(class)'),
]
for name,which,a,b in M:
    src_core,src_plug=core,plug
    if which=='core':
        assert src_core.count(a)==1,(name,'bulunamadı'); src_core=src_core.replace(a,b)
    else:
        assert src_plug.count(a)==1,(name,'bulunamadı'); src_plug=src_plug.replace(a,b)
    import tempfile
    d=tempfile.mkdtemp()
    open(os.path.join(d,'m_core.lua'),'w',encoding='utf-8').write(src_core)
    open(os.path.join(d,'m_plug.lua'),'w',encoding='utf-8').write(src_plug)
    outs=[]
    for t in [('test_core.lua',), ('test_plugin.lua',)]:
        env=dict(os.environ, NODE_PATH=os.path.join(HERE,'..','..','assistant','tools','vendor'))
        r=subprocess.run(['node',os.path.join(HERE,'run.js'),os.path.join(HERE,t[0]),'core='+os.path.join(d,'m_core.lua'),'plugin='+os.path.join(d,'m_plug.lua')],capture_output=True,text=True,timeout=120,env=env)
        outs.append((r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else '?')
    out=[' | '.join(outs)]
    caught = any(not o.split(':')[0].endswith('GEÇTİ') and 'GEÇTİ' not in o for o in outs)
    print(('YAKALANDI ' if caught else 'KAÇTI    ')+name+'  ->  '+(out[0][:90] if out else r.stderr[:90]))
