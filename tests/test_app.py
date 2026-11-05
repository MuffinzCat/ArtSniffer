from artsniffer import main


def test_app(capsys):
    main()
    out = capsys.readouterr()
    assert "Hello from artsniffer!\n" == out.out
